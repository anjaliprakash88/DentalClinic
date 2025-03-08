from django.db import models
from RECEPTION.models import Patient

class PatientExamination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='examinations')
    # ------------------------------
    # Quadrant 1: Upper Right (Teeth 1–8)
    # ------------------------------
    tooth_1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 1 (Upper Right Third Molar)")
    tooth_2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 2 (Upper Right Second Molar)")
    tooth_3 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 3 (Upper Right First Molar)")
    tooth_4 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 4 (Upper Right Second Premolar)")
    tooth_5 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 5 (Upper Right First Premolar)")
    tooth_6 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 6 (Upper Right Canine)")
    tooth_7 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 7 (Upper Right Lateral Incisor)")
    tooth_8 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 8 (Upper Right Central Incisor)")
    # ------------------------------
    # Quadrant 2: Upper Left (Teeth 9–16)
    # ------------------------------
    tooth_9 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 9 (Upper Left Central Incisor)")
    tooth_10 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 10 (Upper Left Lateral Incisor)")
    tooth_11 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 11 (Upper Left Canine)")
    tooth_12 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 12 (Upper Left First Premolar)")
    tooth_13 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 13 (Upper Left Second Premolar)")
    tooth_14 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 14 (Upper Left First Molar)")
    tooth_15 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 15 (Upper Left Second Molar)")
    tooth_16 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 16 (Upper Left Third Molar)")
    # ------------------------------
    # Quadrant 3: Lower Left (Teeth 17–24)
    # ------------------------------
    tooth_17 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 17 (Lower Left Third Molar)")
    tooth_18 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 18 (Lower Left Second Molar)")
    tooth_19 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 19 (Lower Left First Molar)")
    tooth_20 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 20 (Lower Left Second Premolar)")
    tooth_21 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 21 (Lower Left First Premolar)")
    tooth_22 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 22 (Lower Left Canine)")
    tooth_23 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 23 (Lower Left Lateral Incisor)")
    tooth_24 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 24 (Lower Left Central Incisor)")
    # ------------------------------
    # Quadrant 4: Lower Right (Teeth 25–32)
    # ------------------------------
    tooth_25 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 25 (Lower Right Central Incisor)")
    tooth_26 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 26 (Lower Right Lateral Incisor)")
    tooth_27 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 27 (Lower Right Canine)")
    tooth_28 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 28 (Lower Right First Premolar)")
    tooth_29 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 29 (Lower Right Second Premolar)")
    tooth_30 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 30 (Lower Right First Molar)")
    tooth_31 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 31 (Lower Right Second Molar)")
    tooth_32 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tooth 32 (Lower Right Third Molar)")

    # Fields for general examination
    blood_pressure = models.CharField(max_length=50, blank=True, null=True, verbose_name="Blood Pressure")
    temperature = models.CharField(max_length=50, blank=True, null=True, verbose_name="Temperature")
    pulse_rate = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pulse Rate")
    respiratory_rate = models.CharField(max_length=50, blank=True, null=True, verbose_name="Respiratory Rate")
    weight = models.CharField(max_length=50, blank=True, null=True, verbose_name="Weight")
    height = models.CharField(max_length=50, blank=True, null=True, verbose_name="Height")
    bmi = models.CharField(max_length=50, blank=True, null=True, verbose_name="BMI")
    general_observations = models.TextField(blank=True, null=True, verbose_name="General Observations")
    diagnosis = models.TextField(blank=True, null=True, verbose_name="Diagnosis")
    treatment_plan = models.TextField(blank=True, null=True, verbose_name="Treatment Plan")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"Examination for {self.patient.first_name} {self.patient.last_name} on {self.created_at}"

    class Meta:
        verbose_name = "Patient Examination"
        verbose_name_plural = "Patient Examinations"
