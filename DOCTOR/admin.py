from django.contrib import admin
from .models import Tooth,Treatment, DentalChart, Quadrant, GeneralExamination

admin.site.register(Tooth)
admin.site.register(Treatment)
admin.site.register(DentalChart)
admin.site.register(Quadrant)
admin.site.register(GeneralExamination)
