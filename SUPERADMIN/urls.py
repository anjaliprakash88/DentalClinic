from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.SuperAdminLogin.as_view(), name='superadmin_login'),
    path('signup/', views.SuperAdmin_Signup.as_view(), name='superadmin_signup'),

    path('superadmindashboard/', views.SuperAdminDashboard.as_view(), name='superadmindashboard'),

    path('doctor-create/', views.DoctorCreate.as_view(), name='Doctor-Create'),
   path('specializations/', views.get_specializations, name='specializations'),
]