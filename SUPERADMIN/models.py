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

#--------------SUPPLIER MODEL--------------
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField()
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# ---------------PHARMACEUTICAL MEDICINE MODEL---------------
class PharmaceuticalMedicine(models.Model):
    medicine_name = models.CharField(max_length=255)  # Required
    medicine_type = models.CharField(
        max_length=100,
        choices=[
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('syrup', 'Syrup'),
            ('gel', 'Gel'),
            ('injection', 'Injection'),
            ('other', 'Other')
        ],
        null=True, blank=True
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=50, choices=[
        ('painkiller', 'Painkiller'),
        ('antibiotic', 'Antibiotic'),
        ('anesthetic', 'Anesthetic'),
        ('antiseptic', 'Antiseptic'),
        ('other', 'Other'),
    ], default='other')
    batch_number = models.CharField(max_length=100, unique=True)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5, help_text="Minimum stock level before reorder.")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    storage_instructions = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        from datetime import date
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False

    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    def __str__(self):
        return f"{self.medicine_name} ({self.batch_number})"