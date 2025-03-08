from django.db import models
from SUPERADMIN.models import (Branch,
                               Doctor)

#---------------Patient Registration Form---------------
class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=15, null=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    address = models.TextField(null=True)
    patient_code = models.CharField(max_length=20, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.patient_code:
            last_patient = Patient.objects.filter(branch=self.branch).order_by('-id').first()
            if last_patient:
                last_number = int(last_patient.patient_code[len(self.branch.branch_code):])
                new_number = last_number + 1
            else:
                new_number = 1

            self.patient_code = f"{self.branch.branch_code}{new_number}"

        super().save(*args, **kwargs)  #

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.patient_code})"

#---------------Patient Booking Form---------------
class PatientBooking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bookings')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_appointments')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branch_appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    comments = models.TextField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False) # New field
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'appointment_date', 'appointment_time')

    def __str__(self):
        return f"Booking for {self.patient.first_name} {self.patient.last_name} with {self.doctor} on {self.appointment_date} at {self.appointment_time}"

