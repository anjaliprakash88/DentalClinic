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
    template_name = "doctor/dental-chart.html"

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            charts = DentalChart.objects.all()
            serializer = DentalChartSerializer(charts, many=True)
            return Response(serializer.data, safe=False)
        return render(request, self.template_name)


    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            selected_teeth = data.get("selected_teeth", [])
            status = data.get("status")
            treatment_plan = data.get("treatment_plan", [])
            patient_id = data.get("patient_id")

            # Ensure a dental chart exists for the patient
            dental_chart, created = DentalChart.objects.get_or_create(patient_id=patient_id)

            for tooth in selected_teeth:
                Tooth.objects.update_or_create(
                    dental_chart=dental_chart,
                    tooth_number=tooth["number"],
                    quadrant=tooth["quadrant"],
                    defaults={"status": status, "treatment_plan": ",".join(treatment_plan)}
                )

            return Response({"message": "Data saved successfully!"}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)



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

