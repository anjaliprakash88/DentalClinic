from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPERADMIN.models import PharmaceuticalMedicine, Doctor
from RECEPTION.models import PatientBooking, Patient
from datetime import date
from django.db.models.functions import TruncDate
from .models import (DentalExamination,
                     GeneralExamination,
                     TreatmentNote,
                     TreatmentBill,
                     MedicinePrescription)


class TreatmentBillSerializer(serializers.ModelSerializer):
    treatments = serializers.SerializerMethodField()  # Fetch treatments from JSONField
    balance_amount = serializers.SerializerMethodField()  # Auto-calculate balance

    class Meta:
        model = TreatmentBill
        fields = ['id', 'booking', 'dental_examination', 'treatments', 'total_amount', 'paid_amount', 'balance_amount',
                  'created_at']

    def get_treatments(self, obj):
        return obj.get_treatments()

    def get_balance_amount(self, obj):
        total_amount = obj.total_amount if obj.total_amount is not None else 0
        paid_amount = obj.paid_amount if obj.paid_amount is not None else 0
        return total_amount - paid_amount

    def update(self, instance, validated_data):
        instance.total_amount = validated_data.get("total_amount", instance.total_amount) or 0
        instance.paid_amount = validated_data.get("paid_amount", instance.paid_amount) or 0

        # Auto-update balance amount
        instance.balance_amount = instance.total_amount - instance.paid_amount

        instance.save()
        return instance


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

# ---------------DOCTOR LOGIN SERIALIZER---------------
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

# ---------------------------------------------------
class PreviousPrescriptionSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.medicine_name', read_only=True)

    class Meta:
        model = MedicinePrescription
        fields = ['id', 'medicine_name', 'dosage_days', 'medicine_times', 'meal_times']

class PreviousTreatmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    last_appointment_date = serializers.SerializerMethodField()

    # Fetch previous appointment's records
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

    def get_last_booking(self, obj):
        """ Helper function to fetch the last previous appointment """
        return PatientBooking.objects.filter(
            patient=obj.patient
        ).exclude(id=obj.id).order_by('-appointment_date').first()

    def get_dental_examinations(self, obj):
        last_booking = self.get_last_booking(obj)
        if last_booking:
            return DentalExaminationSerializer(last_booking.dental_examinations.all(), many=True).data
        return []

    def get_treatment_bills(self, obj):
        last_booking = self.get_last_booking(obj)
        if last_booking:
            return TreatmentBillSerializer(last_booking.treatment_bills.all(), many=True).data
        return []

    def get_prescriptions(self, obj):
        last_booking = self.get_last_booking(obj)
        if last_booking:
            return PreviousPrescriptionSerializer(last_booking.prescriptions.all(), many=True).data
        return []

    def get_treatment_notes(self, obj):
        last_booking = self.get_last_booking(obj)
        if last_booking:
            return TreatmentNoteSerializer(last_booking.treatment_notes.all(), many=True).data
        return []




# ---------------------------------------------
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'age', 'phone', 'gender']



class DoctorPatientSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patients = serializers.SerializerMethodField()  # Use a method to get actual patients

    class Meta:
        model = Doctor
        fields = ['doctor_name', 'specialization', 'experience_years', 'qualification', 'phone_number', 'patients']

    def get_doctor_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_patients(self, obj):
        """
        Fetches unique patients who have booked an appointment with the doctor.
        """
        bookings = PatientBooking.objects.filter(doctor=obj).select_related('patient')
        unique_patients = {booking.patient for booking in bookings}  # Get unique patients
        return PatientSerializer(unique_patients, many=True).data