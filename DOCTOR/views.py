from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect
from django.urls import reverse
from .serializer import (DoctorLoginSerializer,
                         GeneralExaminationSerializer,
                         DentalExaminationSerializer,
                         TreatmentNoteSerializer,
                         PrescriptionSerializer,
                         MedicineSerializer,
                         TreatmentBillSerializer,
                         PreviousTreatmentSerializer,
                         DoctorPatientSerializer)
from RECEPTION.serializer import PatientBookingSerializer

from .models import (GeneralExamination,
                     DentalExamination,
                    TreatmentBill
                    )
from SUPERADMIN.models import Doctor, PharmaceuticalMedicine
from RECEPTION.models import PatientBooking, Patient
from django.shortcuts import get_object_or_404,render
from django.utils.timezone import now



class DoctorPatientListView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'doctor/doctor_patient_list.html'

    def get(self, request, doctor_id):
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Get all bookings for this doctor
        bookings = PatientBooking.objects.filter(doctor=doctor).order_by('-appointment_date')
        previous_treatments = PreviousTreatmentSerializer(bookings, many=True).data  # Serialize multiple bookings

        serializer = DoctorPatientSerializer(doctor)

        if request.accepted_renderer.format == 'html':  # Render HTML if requested
            return render(request, self.template_name, {
                "doctor": doctor,
                "patients": serializer.data['patients'],
                "previous_treatments": previous_treatments  # Pass previous treatments
            })

        return Response({"doctor": serializer.data, "previous_treatments": previous_treatments})

    # ------------------------------------------
class PreviousTreatmentView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'doctor/previous_treatment.html'

    def get(self, request, id, format=None):
        booking = get_object_or_404(PatientBooking, id=id)
        serializer = PreviousTreatmentSerializer(booking)

        if request.accepted_renderer.format == 'html':
            return Response({"data": serializer.data}, template_name=self.template_name)

        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------------
class TreatmentBillView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'doctor/treatment_bill.html'

    def get(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient
        patient_name = f"{patient.first_name} {patient.last_name}"
        patient_age = patient.age
        current_datetime = now().strftime("%Y-%m-%d %H:%M:%S")

        dental_examination = DentalExamination.objects.filter(booking=booking).first()
        if not dental_examination:
            return Response(
                {"error": "No dental examination found for this booking."},
                status=status.HTTP_400_BAD_REQUEST
            )

        treatment_bill, created = TreatmentBill.objects.get_or_create(
            booking=booking,
            dental_examination=dental_examination,
            defaults={'total_amount': 0.00, 'paid_amount': 0.00}
        )

        serializer = TreatmentBillSerializer(treatment_bill)

        response_data = {
            "patient_name": patient_name,
            "patient_age": patient_age,
            "current_datetime": current_datetime,
            "booking_id": booking.id,
            "total_amount": serializer.data["total_amount"],
            "paid_amount": serializer.data["paid_amount"],
            "balance_amount": serializer.data["balance_amount"],  # Auto-calculated
            "treatments": serializer.data["treatments"]
        }

        if request.accepted_renderer.format == 'html':
            return Response(response_data, template_name=self.template_name)
        return Response({"treatment_bill": serializer.data, **response_data}, status=status.HTTP_200_OK)

    def post(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        dental_examination = DentalExamination.objects.filter(booking=booking).first()
        if not dental_examination:
            return Response(
                {"error": "No dental examination found for this booking."},
                status=status.HTTP_400_BAD_REQUEST
            )

        treatment_bill, created = TreatmentBill.objects.get_or_create(
            booking=booking,
            dental_examination=dental_examination
        )

        serializer = TreatmentBillSerializer(treatment_bill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Update PatientBooking status when the bill is updated
            booking.status = "Completed"
            booking.save()

            return Response(
                {"message": "Treatment bill updated successfully!", "data": serializer.data,
                 "updated_status": booking.status},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----------------------------------------------------------
class MedicineAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "doctor/prescription.html"

    def get(self, request, booking_id, *args, **kwargs):
        medicines = PharmaceuticalMedicine.objects.all()
        doctor = get_object_or_404(Doctor, user=request.user)
        booking = get_object_or_404(PatientBooking, id=booking_id)

        if request.accepted_renderer.format == "html":
            return render(request, self.template_name, {'medicines': medicines, 'booking': booking})

        serializer = MedicineSerializer(medicines, many=True)
        return Response({'medicines': serializer.data})

    def post(self, request, booking_id, *args, **kwargs):
        doctor = get_object_or_404(Doctor, user=request.user)
        booking = get_object_or_404(PatientBooking, id=booking_id)

        if not booking:
            return Response({"error": "Booking ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        medicines_data = request.data.get('medicines', [])
        if not medicines_data:
            return Response({"error": "No medicine data provided"}, status=status.HTTP_400_BAD_REQUEST)

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

        return Response(
            {"success": True, "created_prescriptions": created_prescriptions},
            status=status.HTTP_201_CREATED
        )

# -------------------------------------------------
class TreatmentSummaryView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = "doctor/treatment_summary.html"

    def get(self, request, booking_id, *args, **kwargs):
        doctor = get_object_or_404(Doctor, user=request.user)
        booking = get_object_or_404(PatientBooking, id=booking_id, doctor=doctor)

        serialized_booking = PatientBookingSerializer(booking)

        if request.accepted_renderer.format == "html":
            return render(request, self.template_name, {"booking": serialized_booking.data})

        return Response(serialized_booking.data, status=status.HTTP_200_OK)

    def post(self, request, booking_id, format=None):
        doctor = get_object_or_404(Doctor, user=request.user)
        booking = get_object_or_404(PatientBooking, id=booking_id, doctor=doctor)

        # Get the data and ensure it includes booking ID
        data = request.data.copy()
        if 'booking' not in data:
            data['booking'] = booking_id  # Add booking ID if not present

        section = data.get("section")

        if section == "treatment_note":
            serializer = TreatmentNoteSerializer(data=data)


        if serializer.is_valid():
            serializer.save()  # booking is already in the validated data
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GeneralExaminationAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "doctor/general_examination.html"

    def get(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        last_exam = GeneralExamination.objects.filter(patient=patient).order_by("-created_at").first()
        if last_exam:
            prev_data = GeneralExaminationSerializer(last_exam).data
            print("✅ Previous Exam Data Found:", prev_data)  # Debugging
        else:
            prev_data = None
            print("❌ No Previous Exam Data Found")  # Debuggi
        prev_data = GeneralExaminationSerializer(last_exam).data if last_exam else None

        # Handle JSON response for AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return Response({"previous_data": prev_data})

        return render(request, self.template_name, {"previous_data": prev_data, "booking_id": booking_id})

    def post(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        try:
            # Use DRF request.data instead of manually decoding JSON
            serializer = GeneralExaminationSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save(patient=patient, booking=booking)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaediatricDentalExaminationView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'doctor/paediatric_dental_examination.html'

    def get(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        last_exam = DentalExamination.objects.filter(patient=patient).order_by("-created_at").first()
        prev_data = DentalExaminationSerializer(last_exam).data if last_exam else None

        # Handle JSON response for AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return Response({"previous_data": prev_data})

        return render(request, self.template_name, {
            "previous_data": prev_data,
            "booking_id": booking_id,
            "patient_id": patient.id  # ✅ Make sure patient_id is sent to the template
        })

    def post(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        selected_teeth = request.data.get('selected_teeth')
        treatments = request.data.get('treatments')


        if not booking_id or not selected_teeth or not treatments or not booking_id:
            return Response({"error": "Missing required data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=booking_id)
            booking = PatientBooking.objects.get(id=booking_id)

            record = DentalExamination.objects.create(
                patient=patient,
                booking=booking,
                selected_teeth=selected_teeth,
                treatments=treatments
            )

            serializer = DentalExaminationSerializer(record)

            if format == 'html':
                return Response({'record': serializer.data}, template_name=self.template_name)

            return Response({"message": "Treatment saved successfully", "data": serializer.data},
                            status=status.HTTP_201_CREATED)

        except Patient.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        except PatientBooking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)




class DentalExaminationView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'doctor/dental_examination.html'

    def get(self, request, booking_id, *args, **kwargs):
        print(f"Received booking_id: {booking_id}")
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        last_exam = DentalExamination.objects.filter(patient=patient).order_by("-created_at").first()
        prev_data = DentalExaminationSerializer(last_exam).data if last_exam else None

        # Handle JSON response for AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return Response({"previous_data": prev_data})

        return render(request, self.template_name, {
            "previous_data": prev_data,
            "booking_id": booking_id,
            "patient_id": patient.id  # ✅ Make sure patient_id is sent to the template
        })

    def post(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient
        print(f"Booking ID: {booking_id}, Patient ID: {patient.id}")

        selected_teeth = request.data.get("selected_teeth")
        treatments = request.data.get("treatments")

        if not selected_teeth or not treatments:
            return Response({"error": "Missing required data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            record = DentalExamination.objects.create(
                patient=patient,
                booking=booking,
                selected_teeth=selected_teeth,
                treatments=treatments,
            )

            serializer = DentalExaminationSerializer(record)
            return Response(
                {"message": "Treatment saved successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

