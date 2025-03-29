from django.contrib import admin
# from .models import (DentalExamination,
#                      GeneralExamination,
#                      TreatmentNote,
#                      MedicinePrescription,
#                      TreatmentBill)

# admin.site.register(DentalExamination,)
# admin.site.register(GeneralExamination)
# admin.site.register(TreatmentNote)
# admin.site.register(MedicinePrescription)
# admin.site.register(TreatmentBill)

from .models import (DentalExamination,
                     MedicinePrescription,
                     TreatmentBill)
admin.site.register(DentalExamination)
admin.site.register(MedicinePrescription)
admin.site.register(TreatmentBill)