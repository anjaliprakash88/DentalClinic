from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPERADMIN.models import PharmaceuticalMedicine
from RECEPTION.models import PatientBooking
from datetime import date
from .models import (DentalExamination,
                     GeneralExamination,
                     TreatmentNote,
                     TreatmentBill,
                     MedicinePrescription)

# --------------------------------------------------------
class TreatmentBillSerializer(serializers.ModelSerializer):
    treatments = serializers.SerializerMethodField()  # Fetch treatments from JSONField

    class Meta:
        model = TreatmentBill
        fields = ['id', 'booking', 'dental_examination', 'treatments', 'price']

    def get_treatments(self, obj):
        return obj.get_treatments()


#--------------------------------------------------
class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmaceuticalMedicine
        fields = ['id', 'medicine_name']


class PrescriptionSerializer(serializers.ModelSerializer):
    medicine = serializers.PrimaryKeyRelatedField(
        queryset=PharmaceuticalMedicine.objects.all()
    )
    medicine_times = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    meal_times = serializers.ListField(
        child=serializers.CharField(), required=False
    )

    class Meta:
        model = MedicinePrescription
        fields = ['id', 'medicine', 'dosage_days', 'medicine_times', 'meal_times','booking']
        read_only_fields = ['id']

    def create(self, validated_data):
        return MedicinePrescription.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.medicine = validated_data.get("medicine", instance.medicine)
        instance.dosage_days = validated_data.get("dosage_days", instance.dosage_days)
        instance.medicine_times = validated_data.get("medicine_times", instance.medicine_times)
        instance.meal_times = validated_data.get("meal_times", instance.meal_times)

        instance.save()
        return instance


# --------------------------------------------------------------
class TreatmentNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentNote
        fields = '__all__'

    def create(self, validated_data):
        booking = validated_data.pop('booking')  # Remove and store booking
        treatment_note = TreatmentNote.objects.create(booking=booking, **validated_data)
        return treatment_note

# ------------------------------------------------------------
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

# --------------DENTAL EXAMINATION--------------
class DentalExaminationSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DentalExamination
        fields = '__all__'
        extra_fields = ['patient_name']

    def get_patient_name(self, obj):
        return f"{obj.booking.patient.first_name} {obj.booking.patient.last_name}" if obj.booking.patient else None

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


class PreviousTreatmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    last_appointment_date = serializers.SerializerMethodField()

    # Custom filtering to exclude today's records
    dental_examinations = serializers.SerializerMethodField()
    treatment_bills = serializers.SerializerMethodField()
    prescriptions = serializers.SerializerMethodField()
    treatment_notes = serializers.SerializerMethodField()

    class Meta:
        model = PatientBooking
        fields = ['id', 'patient_name', 'appointment_date', 'last_appointment_date',
                  'dental_examinations', 'treatment_bills', 'prescriptions', 'treatment_notes']

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient else None

    def get_last_appointment_date(self, obj):
        """ Fetch the last appointment date of this patient (excluding today) """
        last_booking = PatientBooking.objects.filter(
            patient=obj.patient
        ).exclude(id=obj.id).exclude(appointment_date=date.today()).order_by('-appointment_date').first()

        return last_booking.appointment_date if last_booking else None

    def get_dental_examinations(self, obj):
        exams = obj.dental_examinations.all()  # Fetch all first
        print("All Dental Examinations:", exams)  # Debugging
        filtered_exams = exams.exclude(created_at__date=date.today())
        print("Filtered Examinations:", filtered_exams)  # Debugging
        return DentalExaminationSerializer(filtered_exams, many=True).data

    def get_treatment_bills(self, obj):
        bills = obj.treatment_bills.all()
        print("All Treatment Bills:", bills)  # Debugging
        filtered_bills = bills.exclude(created_at__date=date.today())
        print("Filtered Bills:", filtered_bills)  # Debugging
        return TreatmentBillSerializer(filtered_bills, many=True).data

    def get_prescriptions(self, obj):
        prescriptions = obj.prescriptions.all()
        print("All Prescriptions:", prescriptions)  # Debugging
        filtered_prescriptions = prescriptions.exclude(created_at__date=date.today())
        print("Filtered Prescriptions:", filtered_prescriptions)  # Debugging
        return PrescriptionSerializer(filtered_prescriptions, many=True).data

    def get_treatment_notes(self, obj):
        notes = obj.treatment_notes.all()
        print("All Treatment Notes:", notes)  # Debugging
        filtered_notes = notes.exclude(created_at__date=date.today())
        print("Filtered Notes:", filtered_notes)  # Debugging
        return TreatmentNoteSerializer(filtered_notes, many=True).data