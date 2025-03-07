from django.db import models
from django.contrib.auth.models import AbstractUser

# ---------------USER MODEL---------------
class User(AbstractUser):
    is_superadmin = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_reception = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ---------------SUPER-ADMIN MODEL---------------
class SuperAdmin(models.Model):
    user = models.OneToOneField(User, related_name="super_admin", on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, null=True)
    designation = models.CharField(max_length=100, default="Clinic Administrator")

    def __str__(self):
        return self.user.username

# ----------------BRANCH MODEL-------------
class Branch(models.Model):
    branch_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# ---------------DOCTOR MODEL-------------
class Doctor(models.Model):
    user = models.OneToOneField(User, related_name="doctor", on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', related_name="doctors", on_delete=models.CASCADE)

    specialization = models.CharField(
        max_length=100,
        choices=[
            ('General Dentist', 'General Dentist'),
            ('Orthodontist', 'Orthodontist'),
            ('Periodontist', 'Periodontist'),
            ('Endodontist', 'Endodontist'),
            ('Prosthodontist', 'Prosthodontist')
        ]
    )
    experience_years = models.PositiveIntegerField()
    qualification = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, null=True)

    # Certificate & License Uploads
    educational_certificate = models.FileField(upload_to='DOCTOR/certificates/', null=True, blank=True)
    medical_license = models.FileField(upload_to='DOCTOR/licenses/', null=True, blank=True)

    def __str__(self):
        return self.user.username
