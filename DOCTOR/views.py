from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect
from django.urls import reverse
from .serializer import (DoctorLoginSerializer,
                         GeneralExaminationSerializer,
                         DentalExaminationSerializer)
from RECEPTION.serializer import PatientBookingSerializer
from .models import GeneralExamination, DentalExamination
from SUPERADMIN.models import Doctor
from RECEPTION.models import PatientBooking, Patient
from django.shortcuts import get_object_or_404,render
from django.utils.timezone import now



class GeneralExaminationAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "doctor/general_examination.html"

    def get(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient

        last_exam = GeneralExamination.objects.filter(patient=patient).order_by("-created_at").first()
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



# -------------------------- DOCTOR DASHBOARD --------------------------
class DoctorDashboard(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'doctor/doctor-dashboard.html'

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

# -------------- DOCTOR LOGIN ---------------
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

