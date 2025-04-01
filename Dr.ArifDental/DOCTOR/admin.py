from django.contrib import admin
from .models import (DentalExamination,
                     MedicinePrescription,
                     TreatmentBill,
                     Investigation,
                     Dentition,
                     DentitionTreatment)
admin.site.register(DentalExamination)
admin.site.register(MedicinePrescription)
admin.site.register(TreatmentBill)
admin.site.register(Investigation)
admin.site.register(Dentition)
admin.site.register(DentitionTreatment)