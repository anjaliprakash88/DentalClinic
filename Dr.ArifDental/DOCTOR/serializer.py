from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPER_ADMIN.models import PharmaceuticalMedicine, Doctor, Branch, User
from RECEPTION.models import PatientBooking, Patient
from .models import (DentalExamination,
                     MedicinePrescription,
                     TreatmentBill,
                     Investigation,
                     DentitionTreatment,
                     Dentition,
                     Diagnosis)

#-------------DOCTOR CHANGE PASSWORD---------------
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
    
# --------------DENTAL EXAMINATION--------------
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'email', 'phone', 'age', 'gender', 'address']
class PatientBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientBooking
        fields = ['id', 'appointment_date', 'appointment_time', 'reason', 'status']
class InvestigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investigation
        fields = ['id', 'image', 'uploaded_at']
class DentalExaminationSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    booking = PatientBookingSerializer(read_only=True)
    investigations = InvestigationSerializer(many=True, read_only=True)

    class Meta:
        model = DentalExamination
        fields = [
            'id', 'patient', 'booking', 'chief_complaints', 'history_of_present_illness',
            'medical_history', 'personal_history', 'general_examination', 'general_examination_intraoral',
            'local_examination_extraoral', 'soft_tissue', 'periodontal_status', 'treatment_plan',
            'created_at', 'updated_at', 'investigations'
        ]

# --------------DIAGNOSIS--------------
class DiagnosisSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    booking = PatientBookingSerializer(read_only=True)

    class Meta:
        model = Diagnosis
        fields = ['id', 'patient', 'booking', 'diagnosis', 'created_at', 'updated_at']

# ----------------DENTITION-------------
class DentitionTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DentitionTreatment
        fields = ['id', 'name', 'color_code']
class DentitionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    booking = PatientBookingSerializer(read_only=True)
    treatment = DentitionTreatmentSerializer(read_only=True)

    class Meta:
        model = Dentition
        fields = ['id', 'patient', 'booking', 'selected_teeth', 'treatment', 'note', 'created_at']

    def create(self, validated_data):
        # Create DentitionTreatment first if it doesn't exist and then save Dentition
        treatment_data = validated_data.pop('treatment', None)

        # Handle treatment if provided, otherwise leave it as null
        if treatment_data:
            treatment_instance = DentitionTreatment.objects.create(**treatment_data)
            validated_data['treatment'] = treatment_instance

        dentition_instance = Dentition.objects.create(**validated_data)
        return dentition_instance

    def update(self, instance, validated_data):
        # Update DentitionTreatment if treatment data is provided
        treatment_data = validated_data.pop('treatment', None)
        if treatment_data:
            instance.treatment.name = treatment_data.get('name', instance.treatment.name)
            instance.treatment.color_code = treatment_data.get('color_code', instance.treatment.color_code)
            instance.treatment.save()

        instance.selected_teeth = validated_data.get('selected_teeth', instance.selected_teeth)
        instance.note = validated_data.get('note', instance.note)
        instance.save()

        return instance

# ---------------DOCTOR VIEW PROFILE ---------------
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

# ---------------TREATMENT BILL---------------
class TreatmentBillSerializer(serializers.ModelSerializer):
    dental_examination = DentalExaminationSerializer(read_only=True)
    balance_amount = serializers.ReadOnlyField()

    
    class Meta:
        model = TreatmentBill
        fields = ['id', 'booking', 'dental_examination', 'total_amount', 
                  'paid_amount', 'balance_amount', 'created_at','payment_status','payment_method']

# ---------------PRESCRIPTION---------------
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

# ---------------TODAY PREVIEW--------------
class TodayPreviewSerializer(serializers.Serializer):
    patient = PatientSerializer(read_only=True)
    booking = PatientBookingSerializer(read_only=True)
    dental_examination = serializers.SerializerMethodField()
    dentition = serializers.SerializerMethodField()
    diagnosis = serializers.SerializerMethodField()
    medicine_prescription = serializers.SerializerMethodField()
    treatment_bill = serializers.SerializerMethodField()
    investigations = serializers.SerializerMethodField()

    def get_dental_examination(self, obj):
        # Get examination ONLY for this specific booking
        examination = DentalExamination.objects.filter(
            booking=obj  # Use booking reference instead of date
        ).order_by('-created_at').first()
        return DentalExaminationSerializer(examination).data if examination else None

    def get_dentition(self, obj):
        # Get dentition ONLY for this specific booking
        dentition = Dentition.objects.filter(
            booking=obj  # Use booking reference instead of date
        ).order_by('-created_at').first()
        return DentitionSerializer(dentition).data if dentition else None

    def get_diagnosis(self, obj):
        # Get dentition ONLY for this specific booking
        diagnosis = Diagnosis.objects.filter(
            booking=obj  # Use booking reference instead of date
        ).order_by('-created_at').first()
        return DiagnosisSerializer(diagnosis).data if diagnosis else None

    def get_medicine_prescription(self, obj):
        prescription = MedicinePrescription.objects.filter(
            booking=obj  # This is correct
        ).order_by('-created_at').first()
        return PrescriptionSerializer(prescription).data if prescription else None

    def get_treatment_bill(self, obj):
        bill = TreatmentBill.objects.filter(
            booking=obj  # This is correct
        ).order_by('-created_at').first()
        return TreatmentBillSerializer(bill).data if bill else None

    def get_investigations(self, obj):
        # Get investigations through examination for this specific booking
        examination = DentalExamination.objects.filter(
            booking=obj  # Use booking reference instead of date and patient
        ).order_by('-created_at').first()

        if examination:
            investigations = Investigation.objects.filter(dental_examination=examination)
            return InvestigationSerializer(investigations, many=True).data
        return []

# ---------------DOCTOR LOGIN---------------
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

# ---------------LAST APPOINTMENT PREVIEW---------------
class LastAppointmentPreviewSerializer(serializers.Serializer):
    patient = PatientSerializer(read_only=True)
    booking = PatientBookingSerializer(read_only=True)
    dental_examination = serializers.SerializerMethodField()
    dentition = serializers.SerializerMethodField()
    diagnosis = serializers.SerializerMethodField()
    medicine_prescription = serializers.SerializerMethodField()
    investigations = serializers.SerializerMethodField()

    def get_dental_examination(self, obj):
        # This is correct - uses booking reference
        exam = DentalExamination.objects.filter(
            booking=obj
        ).order_by('-created_at').first()
        print("LastAppointment - DentalExamination found:", exam)
        return DentalExaminationSerializer(exam).data if exam else None

    def get_dentition(self, obj):
        # This is correct - uses booking reference
        dentition = Dentition.objects.filter(
            booking=obj
        ).order_by('-created_at').first()
        return DentitionSerializer(dentition).data if dentition else None

    def get_diagnosis(self, obj):
        # This is correct - uses booking reference
        diagnosis = Diagnosis.objects.filter(
            booking=obj
        ).order_by('-created_at').first()
        return DiagnosisSerializer(diagnosis).data if diagnosis else None

    def get_medicine_prescription(self, obj):
        # This is correct - uses booking reference
        prescription = MedicinePrescription.objects.filter(
            booking=obj
        ).order_by('-created_at').first()
        return PrescriptionSerializer(prescription).data if prescription else None

    def get_investigations(self, obj):
        # Fix to use the booking reference instead of date and patient
        exam = DentalExamination.objects.filter(
            booking=obj  # Use booking reference instead of date and patient
        ).order_by('-created_at').first()

        if exam:
            investigations = Investigation.objects.filter(dental_examination=exam)
            return InvestigationSerializer(investigations, many=True).data
        return []

# ---------------PATIENT LIST VIEW---------------
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