from rest_framework import serializers
from .models import PatientBooking



# ---------------PATIENT BOOKING SERIALIZER-------------
class PatientBookingSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    patient_name = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = PatientBooking
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name', 'branch', 'branch_name',
            'appointment_date', 'appointment_time', 'status', 'comments', 'created_at', 'gender', 'age'
        ]

    def get_patient_name(self, obj):
        return f" {obj.patient.patient_code}--{obj.patient.first_name} {obj.patient.last_name}"

    def get_doctor_name(self, obj):
        return obj.doctor.user.username if obj.doctor else None

    def get_gender(self, obj):
        return obj.patient.gender

    def get_age(self, obj):
        return obj.patient.age