from rest_framework import serializers
from django.contrib.auth import authenticate
from SUPERADMIN.models import PharmaceuticalMedicine
from .models import (DentalExamination,
                     GeneralExamination,
                     TreatmentNote,

                     MedicinePrescription)



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

# class QuadrantSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Quadrant
#         fields = '__all__'
#
# class ToothSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Tooth
#         fields = '__all__'
#
# class TreatmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Treatment
#         fields = '__all__'
#
# class DentalChartSerializer(serializers.ModelSerializer):
#     quadrants = QuadrantSerializer(many=True, read_only=True, source='get_quadrants')
#     treatments = serializers.SerializerMethodField()
#
#     class Meta:
#         model = DentalChart
#         fields = ['id', 'patient', 'created_at', 'updated_at', 'quadrants', 'treatments']
#
#     def get_treatments(self, obj):
#         # Fetch all teeth related to this patient's quadrants
#         quadrants = Quadrant.objects.all()
#         teeth = Tooth.objects.filter(quadrant__in=quadrants)
#
#         # Fetch treatments for these teeth
#         treatments = Treatment.objects.filter(tooth__in=teeth)
#         return TreatmentSerializer(treatments, many=True).data


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
