from django.contrib import admin
from .models import DentalExamination, GeneralExamination

admin.site.register(DentalExamination,)
admin.site.register(GeneralExamination)
