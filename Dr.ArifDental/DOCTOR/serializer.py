from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPER_ADMIN.models import PharmaceuticalMedicine, Doctor, Branch, User
from RECEPTION.models import PatientBooking, Patient
from datetime import date
from .models import DentalExamination, MedicinePrescription, TreatmentBill
from django.db.models.functions import TruncDate
# from .models import (DentalExamination,
#                      GeneralExamination,
#                      TreatmentNote,
#                      TreatmentBill,
#                      MedicinePrescription)



#-----------------------------------Doctor Change Password SERIALIZER--------------------------------------
class ChangeDoctorPasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
    
# --------------------------------------------
class DentalExaminationSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = DentalExamination
        fields = [
            'id', 'patient', 'patient_name', 'booking', 'booking_id',
            'chief_complaints', 'history_of_present_illness', 'medical_history',
            'past_dental_history', 'personal_history', 'general_examination',
            'general_examination_intraoral', 'local_examination_extraoral',
            'soft_tissue', 'dentition', 'periodontal_status', 'investigation',
            'treatment_plan', 'doctor_signature', 'patient_signature', 'created_at'
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.full_name}"

# ---------------DOCTOR VIEW PROFILE SERIALIZER---------------
class UserViewProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class DoctorViewProfileSerializer(serializers.ModelSerializer):
    user = UserViewProfileSerializer()
    branch = BranchSerializer()



    class Meta:
        model = Doctor
        fields = '__all__'

    def update(self, instance, validated_data):
        # Update related user fields
        user_data = validated_data.pop('user', {})
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Update doctor fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
# ---------------------------------------------------------
class TreatmentBillSerializer(serializers.ModelSerializer):
    dental_examination = DentalExaminationSerializer(read_only=True)
    balance_amount = serializers.ReadOnlyField()

    
    class Meta:
        model = TreatmentBill
        fields = ['id', 'booking', 'dental_examination', 'total_amount', 
                  'paid_amount', 'balance_amount', 'created_at','payment_status','payment_method']


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
# class TreatmentNoteSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TreatmentNote
#         fields = '__all__'
#
#     def create(self, validated_data):
#         booking = validated_data.pop('booking')  # Remove and store booking
#         treatment_note = TreatmentNote.objects.create(booking=booking, **validated_data)
#         return treatment_note

# ------------------------------------------------------------
# class GeneralExaminationSerializer(serializers.ModelSerializer):
#     patient_name = serializers.CharField(source="patient.name", read_only=True)
#     booking_id = serializers.IntegerField(source="booking.id", read_only=True)
#
#     class Meta:
#         model = GeneralExamination
#         fields = [
#             "id", "patient", "patient_name", "booking", "booking_id", "previous_visit",
#             "previous_sugar_level", "previous_pressure_level", "previous_notes",
#             "sugar_level", "blood_pressure", "notes", "created_at", "updated_at"
#         ]
#         read_only_fields = ["patient", "booking", "previous_visit", "previous_sugar_level", "previous_pressure_level", "previous_notes"]

# --------------DENTAL EXAMINATION--------------
# class DentalExaminationSerializer(serializers.ModelSerializer):
#     patient_name = serializers.SerializerMethodField()
#
#     class Meta:
#         model = DentalExamination
#         fields = '__all__'
#         extra_fields = ['patient_name']
#
#     def get_patient_name(self, obj):
#         return f"{obj.booking.patient.first_name} {obj.booking.patient.last_name}" if obj.booking.patient else None

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
class PreviousTreatmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    last_appointment_date = serializers.SerializerMethodField()

    # Fetch previous appointment's records
    dental_examinations = serializers.SerializerMethodField()
    treatment_bills = serializers.SerializerMethodField()
    prescriptions = serializers.SerializerMethodField()


    class Meta:
        model = PatientBooking
        fields = ['id', 'patient_name', 'appointment_date', 'last_appointment_date',
                  'dental_examinations', 'treatment_bills', 'prescriptions']

    def get_patient_name(self, obj):
        """Return full patient name."""
        return f"{obj.patient.full_name}" if obj.patient else None

    def get_last_appointment_date(self, obj):
        """Fetch the last appointment date of this patient (excluding today)."""
        last_booking = PatientBooking.objects.filter(
            patient=obj.patient
        ).exclude(id=obj.id).exclude(appointment_date=date.today()).order_by('-appointment_date').first()

        return last_booking.appointment_date if last_booking else None

    def get_last_booking(self, obj):
        """Helper function to fetch the last previous appointment."""
        return PatientBooking.objects.filter(
            patient=obj.patient
        ).exclude(id=obj.id).order_by('-appointment_date').first()

    def get_dental_examinations(self, obj):
        """Fetch previous dental examinations."""
        last_booking = self.get_last_booking(obj)
        if last_booking:
            examinations = DentalExamination.objects.filter(booking=last_booking)
            return DentalExaminationSerializer(examinations, many=True).data
        return []

    def get_treatment_bills(self, obj):
        """Fetch previous treatment bills."""
        last_booking = self.get_last_booking(obj)
        if last_booking:
            bills = TreatmentBill.objects.filter(booking=last_booking)
            return TreatmentBillSerializer(bills, many=True).data
        return []

    def get_prescriptions(self, obj):
        """Fetch previous prescriptions."""
        last_booking = self.get_last_booking(obj)
        if last_booking:
            prescriptions = MedicinePrescription.objects.filter(booking=last_booking)
            return PrescriptionSerializer(prescriptions, many=True).data
        return []





# ---------------------------------------------
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id', 'branch', 'full_name', 'email', 'phone', 'age', 'gender',
            'address', 'occupation', 'patient_code', 'created_at',
            'is_active', 'medical_notes'
        ]



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