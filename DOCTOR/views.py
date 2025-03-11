from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework import status
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from django.http import HttpResponseRedirect
from django.urls import reverse
from .serializer import (DoctorLoginSerializer,
                         DentalChartSerializer,
                         GeneralExaminationSerializer)
from RECEPTION.serializer import PatientBookingSerializer
from .models import DentalChart, Tooth, GeneralExamination
from SUPERADMIN.models import Doctor
from RECEPTION.models import PatientBooking, Patient
from django.shortcuts import get_object_or_404,render
from django.utils.timezone import now
import json


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



class DentalChartAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "doctor/dental_examination.html"

    def get(self, request, booking_id):
        """Load the dental chart with correct FDI numbering (1-8 per quadrant)"""
        teeth = []
        quadrant_mapping = {
            1: 10,  # Upper Right Quadrant (11-18)
            2: 20,  # Upper Left Quadrant (21-28)
            3: 40,  # Lower Left Quadrant (41-48)
            4: 30,  # Lower Right Quadrant (31-38)
        }

        for q in range(1, 5):
            for n in range(1, 9):
                teeth.append({
                    "id": f"{q}-{n}",
                    "tooth_number": quadrant_mapping[q] + n,
                    "status": "healthy"
                })

        return Response({"teeth": teeth, "booking_id": booking_id}, template_name=self.template_name)

    def post(self, request, booking_id):
        """Save tooth status & treatment plans"""
        user = request.user
        selected_teeth = request.data.get("teeth", [])
        status = request.data.get("status", "healthy")
        treatments = request.data.get("treatments", [])

        for tooth_id in selected_teeth:
            tooth, created = Tooth.objects.get_or_create(user=user, tooth_number=tooth_id)
            tooth.status = status
            tooth.save()

            for treatment in treatments:
                DentalChart.objects.create(user=user, tooth=tooth, treatment=treatment, booking_id=booking_id)

        return Response({"message": "Data saved successfully!"})




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

