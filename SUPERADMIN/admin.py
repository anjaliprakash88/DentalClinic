from django.contrib import admin
from .models import (User,
                     SuperAdmin,
                     Branch,
                     Doctor,
                     Supplier,
                     PharmaceuticalMedicine)

admin.site.register(User)
admin.site.register(SuperAdmin)
admin.site.register(Branch)
admin.site.register(Doctor)
admin.site.register(Supplier)
admin.site.register(PharmaceuticalMedicine)
