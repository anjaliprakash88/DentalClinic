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



class DentalExamination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="dental_examinations")
    booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="dental_examinations")  # Link to PatientBooking
    selected_teeth = models.JSONField()  # Store selected teeth as a list (e.g., ["11", "12", "13"])
    treatments = models.JSONField()  # Store treatments as a list (e.g., ["filling", "root-canal"])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Treatment for {self.booking.patient.first_name} {self.booking.patient.last_name} on {self.booking.appointment_date}"

