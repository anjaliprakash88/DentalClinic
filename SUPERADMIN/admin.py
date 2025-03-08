from django.contrib import admin
from .models import User, SuperAdmin, Branch, Doctor

admin.site.register(User)
admin.site.register(SuperAdmin)
admin.site.register(Branch)
admin.site.register(Doctor)
