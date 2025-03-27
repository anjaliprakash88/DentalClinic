from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect
from django.urls import reverse
from .serializer import (DoctorLoginSerializer,
                         DentalExaminationSerializer,
                         DoctorViewProfileSerializer,
                         MedicineSerializer,
                         PrescriptionSerializer, 
                         TreatmentBillSerializer,
                         PreviousTreatmentSerializer)
from RECEPTION.serializer import PatientBookingSerializer
from .models import DentalExamination, TreatmentBill

from SUPERADMIN.models import Doctor, PharmaceuticalMedicine
from RECEPTION.models import PatientBooking, Patient
from django.shortcuts import get_object_or_404,render
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse


class Checkup_Page(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "doctor/checkup_page.html"

    def get(self, request, booking_id, format=None):
        """
        Fetch existing dental examination data for a patient.
        If multiple records exist, fetch the latest.
        Excludes 'past_dental_history'.
        """
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        # Fetch the latest or create a new examination record
        examination = (
            DentalExamination.objects.filter(patient=patient, booking=booking)
            .order_by('-created_at')
            .first()
        )

        if examination is None:
            examination = DentalExamination.objects.create(patient=patient, booking=booking)
              
        treatment_bill, created = TreatmentBill.objects.get_or_create(
            booking=booking,
            dental_examination=examination,
            defaults={'patient': patient,'total_amount': 0.00, 'paid_amount': 0.00}
        )
        
        # Serialize data without 'past_dental_history'
        examination_serializer = DentalExaminationSerializer(examination)
        treatment_bill_serializer = TreatmentBillSerializer(treatment_bill)
        # Fetch all available medicines
        medicines = PharmaceuticalMedicine.objects.all()
        medicine_serializer = MedicineSerializer(medicines, many=True)

        if format == 'json':
            return Response({
                "examination": examination_serializer.data,
                "treatment_bill": treatment_bill_serializer.data,
                 "medicines": medicine_serializer.data
            }, status=status.HTTP_200_OK)

        return render(request, self.template_name, {
             "examination": examination_serializer.data,
             "treatment_bill": treatment_bill_serializer.data,
             "medicines": medicine_serializer.data,
             "booking": booking
        })

    def post(self, request, booking_id, format=None):
        """
        Save or update the latest dental examination data, excluding past dental history.
        """
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        # Fetch the latest examination record (if exists), otherwise create a new one
        examination = DentalExamination.objects.filter(patient=patient, booking=booking).order_by('-created_at').first()

        if not examination:
            # Create a new record if no previous examination exists
            examination = DentalExamination.objects.create(patient=patient, booking=booking)

        # Extract data from request
        examination.chief_complaints = request.data.get("chief_complaints", "")
        examination.history_of_present_illness = request.data.get("history_of_present_illness", "")
        examination.medical_history = request.data.get("medical_history", "")
        examination.personal_history = request.data.get("personal_history", "")
        examination.general_examination = request.data.get("general_examination", "")
        examination.general_examination_intraoral = request.data.get("general_examination_intraoral", "")
        examination.local_examination_extraoral = request.data.get("local_examination_extraoral", "")
        examination.soft_tissue = request.data.get("soft_tissue", "")
        examination.periodontal_status = request.data.get("periodontal_status", "")
        examination.treatment_plan = request.data.get("treatment_plan", "")

        # Handle uploaded files
        if 'investigation' in request.FILES:
            examination.investigation = request.FILES['investigation']
        if 'doctor_signature' in request.FILES:
            examination.doctor_signature = request.FILES['doctor_signature']
        if 'patient_signature' in request.FILES:
            examination.patient_signature = request.FILES['patient_signature']

        # Save selected teeth data
        dentition_data = request.data.get("dentition", "[]")
        examination.dentition = dentition_data 
        examination.save() # Assuming `dentition` is a JSONField or TextField

        treatment_bill, created = TreatmentBill.objects.get_or_create(
            booking=booking,
            dental_examination=examination,
            defaults={
                'patient': patient,  # ✅ Ensure patient is explicitly assigned
                'total_amount': 0.00,
                'paid_amount': 0.00,
            }
        )

        # ✅ If `get_or_create` didn't assign `patient`, update it manually
        if not created and not treatment_bill.patient:
            print(f"Fixing missing patient for TreatmentBill {treatment_bill.id}")
            treatment_bill.patient = patient
            treatment_bill.save()

        
        medicines_data = request.data.get('medicines', [])
        created_prescriptions = []
        errors = []

        for med in medicines_data:
            try:
                medicine_id = med.get('medicine')
                medicine = get_object_or_404(PharmaceuticalMedicine, id=medicine_id)

                prescription_data = {
                    'booking': booking.id,  # Pass actual booking instance
                    'medicine': medicine.id,
                    'dosage_days': med.get('dosage_days', 1),
                    'medicine_times': med.get('medicine_times', []),  # Now expects a JSON list
                    'meal_times': med.get('meal_times', [])  # Now expects a JSON list
                }

                serializer = PrescriptionSerializer(data=prescription_data)
                if serializer.is_valid():
                    prescription = serializer.save()
                    created_prescriptions.append(PrescriptionSerializer(prescription).data)
                else:
                    errors.append(serializer.errors)
            except Exception as e:
                errors.append(str(e))

        if errors:
            return Response(
                {"error": "Some medicines could not be saved", "details": errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "message": "Checkup details and medicine prescriptions saved successfully!",
            "examination": DentalExaminationSerializer(examination).data,
            "treatment_bill": TreatmentBillSerializer(treatment_bill).data,
            "created_prescriptions": created_prescriptions
        }, status=status.HTTP_200_OK)


# ----------------------------LOGOUT VIEW------------------------------#
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete the token to log the user out
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out"}, status=200)

#--------------DOCTOR PROFILE VIEW---------------
class DoctorProfileView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'doctor/doctor_profile.html'

    def get(self, request):
        try:
            doctor = get_object_or_404(Doctor, user=request.user)
            doctor_serializer = DoctorViewProfileSerializer(doctor)

            if request.accepted_renderer.format == 'json':
                return Response({'doctors': doctor_serializer.data}, status=status.HTTP_200_OK)
            return Response({'doctors': doctor_serializer.data}, template_name=self.template_name)

        except Doctor.DoesNotExist:
            return Response({'message': 'Doctor profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        doctor = get_object_or_404(Doctor, user=request.user)
        # Extract user-related fields
        user_data = {
            "username": request.data.get("username"),
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "email": request.data.get("email"),
        }

        for attr, value in user_data.items():
            if value:
                setattr(doctor.user, attr, value)
            doctor.user.save()

            # Update Doctor model fields
        doctor_data = {
            "phone_number": request.data.get("phone_number"),
            "experience_years": request.data.get("experience_years"),
            "qualification": request.data.get("qualification"),
            "address": request.data.get("address"),
            "specialization": request.data.get("specialization"),
        }

        for attr, value in doctor_data.items():
            if value:
                setattr(doctor, attr, value)

        if "educational_certificate" in request.FILES:
            doctor.educational_certificate = request.FILES["educational_certificate"]
        if "medical_license" in request.FILES:
            doctor.medical_license = request.FILES["medical_license"]
        doctor.save()
        return Response({"message": "Doctor profile updated successfully"}, status=status.HTTP_200_OK)


# # ------------------------------------------------
# class DoctorPatientListView(APIView):
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     template_name = 'doctor/patient_list.html'
#
#     def get(self, request, doctor_id):
#         doctor = get_object_or_404(Doctor, id=doctor_id)
#
#         # Get all bookings for this doctor
#         bookings = PatientBooking.objects.filter(doctor=doctor).order_by('-appointment_date')
#         previous_treatments = PreviousTreatmentSerializer(bookings, many=True).data  # Serialize multiple bookings
#
#         serializer = DoctorPatientSerializer(doctor)
#
#         if request.accepted_renderer.format == 'html':  # Render HTML if requested
#             return render(request, self.template_name, {
#                 "doctor": doctor,
#                 "patients": serializer.data['patients'],
#                 "previous_treatments": previous_treatments  # Pass previous treatments
#             })
#
#         return Response({"doctor": serializer.data, "previous_treatments": previous_treatments})

#     # ------------------------------------------
class PreviousTreatmentView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'doctor/previous_treatment.html'

    def get(self, request, id, format=None):
        booking = get_object_or_404(PatientBooking, id=id)
        serializer = PreviousTreatmentSerializer(booking)

        if request.accepted_renderer.format == 'html':
            return Response({"data": serializer.data}, template_name=self.template_name)

        return Response(serializer.data, status=status.HTTP_200_OK)


# # ------------------------------
# class TreatmentBillView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'doctor/treatment_bill.html'
#
#     def get(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#         patient_name = f"{patient.first_name} {patient.last_name}"
#         patient_age = patient.age
#         current_datetime = now().strftime("%Y-%m-%d %H:%M:%S")
#
#         dental_examination = DentalExamination.objects.filter(booking=booking).first()
#         if not dental_examination:
#             return Response(
#                 {"error": "No dental examination found for this booking."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         treatment_bill, created = TreatmentBill.objects.get_or_create(
#             booking=booking,
#             dental_examination=dental_examination,
#             defaults={'total_amount': 0.00, 'paid_amount': 0.00}
#         )
#
#         serializer = TreatmentBillSerializer(treatment_bill)
#
#         response_data = {
#             "patient_name": patient_name,
#             "patient_age": patient_age,
#             "current_datetime": current_datetime,
#             "booking_id": booking.id,
#             "total_amount": serializer.data["total_amount"],
#             "paid_amount": serializer.data["paid_amount"],
#             "balance_amount": serializer.data["balance_amount"],  # Auto-calculated
#             "treatments": serializer.data["treatments"]
#         }
#
#         if request.accepted_renderer.format == 'html':
#             return Response(response_data, template_name=self.template_name)
#         return Response({"treatment_bill": serializer.data, **response_data}, status=status.HTTP_200_OK)
#
#     def post(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         dental_examination = DentalExamination.objects.filter(booking=booking).first()
#         if not dental_examination:
#             return Response(
#                 {"error": "No dental examination found for this booking."},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         treatment_bill, created = TreatmentBill.objects.get_or_create(
#             booking=booking,
#             dental_examination=dental_examination
#         )
#
#         serializer = TreatmentBillSerializer(treatment_bill, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#
#             # Update PatientBooking status when the bill is updated
#             booking.status = "Completed"
#             booking.save()
#
#             return Response(
#                 {"message": "Treatment bill updated successfully!", "data": serializer.data,
#                  "updated_status": booking.status},
#                 status=status.HTTP_200_OK
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#-----------------------------------------------------------
class MedicineAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "doctor/checkup_page.html"

    def get(self, request, booking_id, *args, **kwargs):
        medicines = PharmaceuticalMedicine.objects.all()
        doctor = get_object_or_404(Doctor, user=request.user)
        booking = get_object_or_404(PatientBooking, id=booking_id)

        if request.accepted_renderer.format == "html":
            return render(request, self.template_name, {'medicines': medicines, 'booking': booking})

        serializer = MedicineSerializer(medicines, many=True)
        return Response({'medicines': serializer.data})
#
#     def post(self, request, booking_id, *args, **kwargs):
#         doctor = get_object_or_404(Doctor, user=request.user)
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#
#         if not booking:
#             return Response({"error": "Booking ID is required"}, status=status.HTTP_400_BAD_REQUEST)
#
#         medicines_data = request.data.get('medicines', [])
#         if not medicines_data:
#             return Response({"error": "No medicine data provided"}, status=status.HTTP_400_BAD_REQUEST)
#
#         created_prescriptions = []
#         errors = []
#
#         for med in medicines_data:
#             try:
#                 medicine_id = med.get('medicine')
#                 medicine = get_object_or_404(PharmaceuticalMedicine, id=medicine_id)
#
#                 prescription_data = {
#                     'booking': booking.id,  # Pass actual booking instance
#                     'medicine': medicine.id,
#                     'dosage_days': med.get('dosage_days', 1),
#                     'medicine_times': med.get('medicine_times', []),  # Now expects a JSON list
#                     'meal_times': med.get('meal_times', [])  # Now expects a JSON list
#                 }
#
#                 serializer = PrescriptionSerializer(data=prescription_data)
#                 if serializer.is_valid():
#                     prescription = serializer.save()
#                     created_prescriptions.append(PrescriptionSerializer(prescription).data)
#                 else:
#                     errors.append(serializer.errors)
#             except Exception as e:
#                 errors.append(str(e))
#
#         if errors:
#             return Response(
#                 {"error": "Some medicines could not be saved", "details": errors},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         return Response(
#             {"success": True, "created_prescriptions": created_prescriptions},
#             status=status.HTTP_201_CREATED
#         )

# # -------------------------------------------------
# class TreatmentSummaryView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = "doctor/treatment_summary.html"
#
#     def get(self, request, booking_id, *args, **kwargs):
#         doctor = get_object_or_404(Doctor, user=request.user)
#         booking = get_object_or_404(PatientBooking, id=booking_id, doctor=doctor)
#
#         serialized_booking = PatientBookingSerializer(booking)
#
#         if request.accepted_renderer.format == "html":
#             return render(request, self.template_name, {"booking": serialized_booking.data})
#
#         return Response(serialized_booking.data, status=status.HTTP_200_OK)
#
#     def post(self, request, booking_id, format=None):
#         doctor = get_object_or_404(Doctor, user=request.user)
#         booking = get_object_or_404(PatientBooking, id=booking_id, doctor=doctor)
#
#         # Get the data and ensure it includes booking ID
#         data = request.data.copy()
#         if 'booking' not in data:
#             data['booking'] = booking_id  # Add booking ID if not present
#
#         section = data.get("section")
#
#         if section == "treatment_note":
#             serializer = TreatmentNoteSerializer(data=data)
#
#
#         if serializer.is_valid():
#             serializer.save()  # booking is already in the validated data
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
#
# class GeneralExaminationAPIView(APIView):
#     renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
#     template_name = "doctor/general_examination.html"
#
#     def get(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#
#         last_exam = GeneralExamination.objects.filter(patient=patient).order_by("-created_at").first()
#         if last_exam:
#             prev_data = GeneralExaminationSerializer(last_exam).data
#             print("✅ Previous Exam Data Found:", prev_data)  # Debugging
#         else:
#             prev_data = None
#             print("❌ No Previous Exam Data Found")  # Debuggi
#         prev_data = GeneralExaminationSerializer(last_exam).data if last_exam else None
#
#         # Handle JSON response for AJAX
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return Response({"previous_data": prev_data})
#
#         return render(request, self.template_name, {"previous_data": prev_data, "booking_id": booking_id})
#
#     def post(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#
#         try:
#             # Use DRF request.data instead of manually decoding JSON
#             serializer = GeneralExaminationSerializer(data=request.data)
#
#             if serializer.is_valid():
#                 serializer.save(patient=patient, booking=booking)
#                 return Response(serializer.data, status=status.HTTP_201_CREATED)
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#
#
# class PaediatricDentalExaminationView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'doctor/paediatric_dental_examination.html'
#
#     def get(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#
#         last_exam = DentalExamination.objects.filter(patient=patient).order_by("-created_at").first()
#         prev_data = DentalExaminationSerializer(last_exam).data if last_exam else None
#
#         # Handle JSON response for AJAX
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return Response({"previous_data": prev_data})
#
#         return render(request, self.template_name, {
#             "previous_data": prev_data,
#             "booking_id": booking_id,
#             "patient_id": patient.id  # ✅ Make sure patient_id is sent to the template
#         })
#
#     def post(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#
#         selected_teeth = request.data.get('selected_teeth')
#         treatments = request.data.get('treatments')
#
#
#         if not booking_id or not selected_teeth or not treatments or not booking_id:
#             return Response({"error": "Missing required data"}, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             patient = Patient.objects.get(id=booking_id)
#             booking = PatientBooking.objects.get(id=booking_id)
#
#             record = DentalExamination.objects.create(
#                 patient=patient,
#                 booking=booking,
#                 selected_teeth=selected_teeth,
#                 treatments=treatments
#             )
#
#             serializer = DentalExaminationSerializer(record)
#
#             if format == 'html':
#                 return Response({'record': serializer.data}, template_name=self.template_name)
#
#             return Response({"message": "Treatment saved successfully", "data": serializer.data},
#                             status=status.HTTP_201_CREATED)
#
#         except Patient.DoesNotExist:
#             return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
#         except PatientBooking.DoesNotExist:
#             return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
#
#
#
#
# class DentalExaminationView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'doctor/dental_examination.html'
#
#     def get(self, request, booking_id, *args, **kwargs):
#         print(f"Received booking_id: {booking_id}")
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#
#         last_exam = DentalExamination.objects.filter(patient=patient).order_by("-created_at").first()
#         prev_data = DentalExaminationSerializer(last_exam).data if last_exam else None
#
#         # Handle JSON response for AJAX
#         if request.headers.get("X-Requested-With") == "XMLHttpRequest":
#             return Response({"previous_data": prev_data})
#
#         return render(request, self.template_name, {
#             "previous_data": prev_data,
#             "booking_id": booking_id,
#             "patient_id": patient.id  # ✅ Make sure patient_id is sent to the template
#         })
#
#     def post(self, request, booking_id, *args, **kwargs):
#         booking = get_object_or_404(PatientBooking, id=booking_id)
#         patient = booking.patient
#         print(f"Booking ID: {booking_id}, Patient ID: {patient.id}")
#
#         selected_teeth = request.data.get("selected_teeth")
#         treatments = request.data.get("treatments")
#
#         if not selected_teeth or not treatments:
#             return Response({"error": "Missing required data"}, status=status.HTTP_400_BAD_REQUEST)
#
#         try:
#             record = DentalExamination.objects.create(
#                 patient=patient,
#                 booking=booking,
#                 selected_teeth=selected_teeth,
#                 treatments=treatments,
#             )
#
#             serializer = DentalExaminationSerializer(record)
#             return Response(
#                 {"message": "Treatment saved successfully", "data": serializer.data},
#                 status=status.HTTP_201_CREATED,
#             )
#
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#

# -------------------------- DOCTOR DASHBOARD --------------------------
class DoctorDashboard(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'doctor/doctor_dashboard.html'

    def get(self, request, format=None):
        doctor = get_object_or_404(Doctor, user=request.user)
        today_appointment = PatientBooking.objects.filter(
            doctor=doctor,
            appointment_date=now().date(),
            status='Confirmed'
        ).select_related('patient')

        serialized_data = PatientBookingSerializer(today_appointment, many=True).data
        print(serialized_data)
        if request.accepted_renderer.format == 'html':
            return render(request, self.template_name, {"doctor": doctor, "patient_data": serialized_data})

        return Response({"appointments": serialized_data}, status=status.HTTP_200_OK)

# --------------DOCTOR LOGIN---------------
class DoctorLoginView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'doctor/docter_login.html'

    def get(self, request):
        serializer = DoctorLoginSerializer()
        return Response({'serializer': serializer})

    def post(self, request):
        serializer = DoctorLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            Token.objects.get_or_create(user=user)
            return HttpResponseRedirect(reverse('doctor-dashboard'))
        print(serializer.errors)
        return Response({"message": "Invalid credentials", 'serializer': serializer, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

