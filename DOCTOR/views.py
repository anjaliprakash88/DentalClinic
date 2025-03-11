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
from .models import Treatment, Tooth, GeneralExamination, Quadrant, DentalChart
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


class DentalChartUpdateAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "doctor/dental_examination.html"

    def post(self, request, booking_id):
        try:
            print("Received Data:", json.dumps(request.data, indent=2))  # Debugging output

            patient = get_object_or_404(Patient, id=booking_id)

            selected_teeth = request.data.get("teeth", [])
            status = request.data.get("status", "healthy")
            treatments = request.data.get("treatments", [])

            if not isinstance(selected_teeth, list):
                return Response({"error": "Teeth data must be a list"}, status=400)

            formatted_teeth = []
            for item in selected_teeth:
                if isinstance(item, str):
                    formatted_teeth.append({"tooth_number": int(item), "status": status, "treatments": treatments})
                elif isinstance(item, dict):
                    formatted_teeth.append(item)
                else:
                    return Response({"error": "Invalid tooth data format"}, status=400)

            if not formatted_teeth:
                return Response({"error": "No valid teeth selected"}, status=400)

            for tooth_data in formatted_teeth:
                tooth_number = tooth_data.get("tooth_number")
                tooth_status = tooth_data.get("status", "healthy")
                tooth_treatments = tooth_data.get("treatments", [])

                if not tooth_number:
                    return Response({"error": "Invalid tooth number"}, status=400)

                try:
                    quadrant_number = int(str(tooth_number)[0])
                except ValueError:
                    return Response({"error": "Invalid tooth number format"}, status=400)

                quadrant = Quadrant.objects.filter(number=quadrant_number).first()
                if not quadrant:
                    return Response({"error": f"Quadrant {quadrant_number} not found"}, status=404)

                tooth, created = Tooth.objects.get_or_create(quadrant=quadrant, number=tooth_number)
                tooth.status = tooth_status
                tooth.save()

                for treatment in tooth_treatments:
                    Treatment.objects.create(tooth=tooth, treatment_type=treatment)

            return Response({"message": "Data saved successfully!"}, status=200)

        except Exception as e:
            print("Internal Server Error:", str(e))  # Log in Django console
            return Response({"error": "Internal server error"}, status=500, content_type="application/json")




class DentalChartAPIView(APIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = "doctor/dental_examination.html"

    def get(self, request, booking_id):
        booking = get_object_or_404(PatientBooking, id=booking_id)
        patient = booking.patient  # ✅ Fetch Patient directly

        # Fetch or create a DentalChart for the patient
        dental_chart, created = DentalChart.objects.get_or_create(patient=patient)

        # Get all quadrants
        quadrants = Quadrant.objects.all()

        # Get all teeth associated with the quadrants
        teeth = Tooth.objects.filter(quadrant__in=quadrants)

        # Serialize the data
        serializer = DentalChartSerializer(dental_chart)

        # If JSON is requested, return JSON response
        if request.accepted_renderer.format == 'json':
            return Response({
                "dental_chart": serializer.data,
                "teeth": list(teeth.values("id", "number", "quadrant", "status")),
            })

        # If HTML is requested, render template with required data
        return Response({
            "dental_chart": serializer.data,
            "quadrants": quadrants,
            "teeth": teeth,
            "booking_id": booking_id,
        }, template_name=self.template_name)

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

