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



