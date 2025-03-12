from django.contrib import admin
from .models import DentalExamination, GeneralExamination, TreatmentNote

admin.site.register(DentalExamination,)
admin.site.register(GeneralExamination)
admin.site.register(TreatmentNote)
