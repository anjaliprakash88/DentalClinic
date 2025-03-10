from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (Quadrant,
                     Tooth,
                     Treatment,
                     DentalChart,
                     GeneralExamination)



class GeneralExaminationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)

    class Meta:
        model = GeneralExamination
        fields = [
            "id", "patient", "patient_name", "booking", "booking_id", "previous_visit",
            "previous_sugar_level", "previous_pressure_level", "previous_notes",
            "sugar_level", "blood_pressure", "notes", "created_at", "updated_at"
        ]
        read_only_fields = ["patient", "booking", "previous_visit", "previous_sugar_level", "previous_pressure_level", "previous_notes"]


class QuadrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quadrant
        fields = '__all__'


class ToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = '__all__'


class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = '__all__'


class DentalChartSerializer(serializers.ModelSerializer):
    quadrants = QuadrantSerializer(many=True, read_only=True, source='get_quadrants')
    teeth = ToothSerializer(many=True, read_only=True, source='get_teeth')
    treatments = TreatmentSerializer(many=True, read_only=True, source='get_treatments')

    class Meta:
        model = DentalChart
        fields = ['id', 'patient', 'created_at', 'updated_at', 'quadrants', 'teeth', 'treatments']


#-----------------------------------Doctor LOGIN SERIALIZER--------------------------------------
class DoctorLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_doctor:
            raise serializers.ValidationError("You are not authorized as a doctor")
        return {'user': user}
