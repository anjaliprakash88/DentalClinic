from django.db import models
from RECEPTION.models import Patient, PatientBooking


class GeneralExamination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="general_examinations")
    booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="general_examinations")

    # Previous examination details (if available)
    previous_visit = models.DateField(null=True, blank=True)
    previous_sugar_level = models.CharField(max_length=10, null=True, blank=True)
    previous_pressure_level = models.CharField(max_length=20, null=True, blank=True)
    previous_notes = models.TextField(null=True, blank=True)

    # New examination data
    sugar_level = models.CharField(max_length=10, null=True, blank=True)
    blood_pressure = models.CharField(max_length=20,null=True, blank=True)
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Fetch previous examination details before saving
        last_exam = GeneralExamination.objects.filter(patient=self.patient).exclude(id=self.id).order_by(
            "-created_at").first()

        if last_exam:
            self.previous_visit = last_exam.created_at.date()
            self.previous_sugar_level = last_exam.sugar_level
            self.previous_pressure_level = last_exam.blood_pressure
            self.previous_notes = last_exam.notes

        super().save(*args, **kwargs)

    def __str__(self):
        return f"General Examination - {self.patient} ({self.created_at.date()})"



class Quadrant(models.Model):
    QUADRANT_CHOICES = [
        (1, 'Upper Right'),
        (2, 'Upper Left'),
        (3, 'Lower Left'),
        (4, 'Lower Right'),
    ]

    number = models.IntegerField(choices=QUADRANT_CHOICES, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.get_number_display()} - {self.name}"


class Tooth(models.Model):
    TOOTH_STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('carious', 'Carious'),
        ('filled', 'Filled'),
        ('missing', 'Missing'),
        ('needs-cleaning', 'Needs Cleaning'),
    ]

    quadrant = models.ForeignKey(Quadrant, on_delete=models.CASCADE, related_name='teeth')
    number = models.IntegerField()  # Tooth number within the quadrant (e.g., 1-8)
    status = models.CharField(max_length=20, choices=TOOTH_STATUS_CHOICES, default='healthy')

    def __str__(self):
        return f"Tooth {self.quadrant.number}-{self.number} ({self.get_status_display()})"


class Treatment(models.Model):
    TREATMENT_CHOICES = [
        ('filling', 'Filling'),
        ('root-canal', 'Root Canal'),
        ('extraction', 'Extraction'),
        ('crown', 'Crown'),
        ('cleaning', 'Professional Cleaning'),
        ('implant', 'Implant'),
    ]

    tooth = models.ForeignKey(Tooth, on_delete=models.CASCADE, related_name='treatments')
    treatment_type = models.CharField(max_length=20, choices=TREATMENT_CHOICES)
    date = models.DateTimeField(auto_now_add=True)  # Date when the treatment was added

    def __str__(self):
        return f"{self.get_treatment_type_display()} for {self.tooth}"


class DentalChart(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='examinations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dental Chart for {self.patient_name}"

    def get_quadrants(self):
        return Quadrant.objects.all()

    def get_teeth(self):
        return Tooth.objects.filter(quadrant__in=self.get_quadrants())

    def get_treatments(self):
        return Treatment.objects.filter(tooth__in=self.get_teeth())
