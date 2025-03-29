from django.db import models
from RECEPTION.models import Patient, PatientBooking
from SUPER_ADMIN.models import PharmaceuticalMedicine
from decimal import Decimal

class DentalExamination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='dental_examinations')
    booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name='dental_examinations', blank=True, null=True)

    chief_complaints = models.TextField(blank=True, null=True)
    history_of_present_illness = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    past_dental_history = models.TextField(blank=True, null=True)
    personal_history = models.TextField(blank=True, null=True)
    general_examination = models.TextField(blank=True, null=True)
    general_examination_intraoral = models.TextField(blank=True, null=True)
    local_examination_extraoral = models.TextField(blank=True, null=True)
    soft_tissue = models.TextField(blank=True, null=True)
    dentition = models.JSONField(blank=True, null=True)  # Store selected teeth numbers as JSON
    periodontal_status = models.TextField(blank=True, null=True)
    investigation = models.ImageField(upload_to='investigations/', blank=True, null=True)
    treatment_plan = models.TextField(blank=True, null=True)
    doctor_signature = models.ImageField(upload_to='signatures/', default='signatures/default_doctor_signature.png')
    patient_signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for records

    def __str__(self):
        return f"Dental Examination for {self.patient.full_name}"

# -------------------- Medicine Prescription Model --------------------
class MedicinePrescription(models.Model):
    booking = models.ForeignKey(
        PatientBooking, on_delete=models.CASCADE, related_name="prescriptions"
    )
    medicine = models.ForeignKey(
        PharmaceuticalMedicine, on_delete=models.CASCADE, related_name="prescriptions"
    )
    dosage_days = models.IntegerField(default=1)
    medicine_times = models.JSONField()
    meal_times = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.medicine.medicine_name


class TreatmentBill(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="treatment_bills")
    dental_examination = models.ForeignKey(DentalExamination, on_delete=models.CASCADE, related_name="ttreatment_bills")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid')
    ], default='pending')
    payment_method = models.CharField(max_length=20, blank=True)

    def get_treatments(self):
        if isinstance(self.dental_examination.treatments, str):
            try:
                import json
                return json.loads(self.dental_examination.treatments)  # Convert string to JSON
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}
        return self.dental_examination.treatments  # If already a dictionary/list

    @property
    def balance_amount(self):
        total = self.total_amount if self.total_amount is not None else Decimal(0)
        paid = self.paid_amount if self.paid_amount is not None else Decimal(0)
        return total - paid

    def _str_(self):
        return f"Bill for {self.booking.patient.full_name} - ${self.total_amount}"


# -------------------- Treatment Note Model --------------------
# class TreatmentNote(models.Model):
#     booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="treatment_notes")
#     note = models.TextField(null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Treatment Note for {self.booking.patient} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
# -------------------------------------------------------------

# class GeneralExamination(models.Model):
#     patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="general_examinations")
#     booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="general_examinations")
#
#     # Previous examination details (if available)
#     previous_visit = models.DateField(null=True, blank=True)
#     previous_sugar_level = models.CharField(max_length=10, null=True, blank=True)
#     previous_pressure_level = models.CharField(max_length=20, null=True, blank=True)
#     previous_notes = models.TextField(null=True, blank=True)
#
#     # New examination data
#     sugar_level = models.CharField(max_length=10, null=True, blank=True)
#     blood_pressure = models.CharField(max_length=20,null=True, blank=True)
#     notes = models.TextField(blank=True)
#
#     # Timestamps
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def save(self, *args, **kwargs):
#         # Fetch the most recent examination before this one
#         last_exam = GeneralExamination.objects.filter(patient=self.patient).exclude(id=self.id).order_by(
#             "-created_at").first()
#
#         if last_exam:
#             # Ensure previous details are stored only if last_exam exists
#             self.previous_visit = last_exam.created_at.date() if last_exam.created_at else None
#             self.previous_sugar_level = last_exam.sugar_level if last_exam.sugar_level else "N/A"
#             self.previous_pressure_level = last_exam.blood_pressure if last_exam.blood_pressure else "N/A"
#             self.previous_notes = last_exam.notes if last_exam.notes else "N/A"
#
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"General Examination - {self.patient} ({self.created_at.date()})"



# class DentalExamination(models.Model):
#     patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="dental_examinations")
#     booking = models.ForeignKey(PatientBooking, on_delete=models.CASCADE, related_name="dental_examinations")  # Link to PatientBooking
#     selected_teeth = models.JSONField(default=list)
#     treatments = models.JSONField(default=list)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"Treatment for {self.booking.patient.first_name} {self.booking.patient.last_name} on {self.booking.appointment_date}"



