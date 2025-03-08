from django.contrib import admin
from .models import PatientBooking, Patient

admin.site.register(Patient)
admin.site.register(PatientBooking)
