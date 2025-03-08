from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.DoctorLoginView.as_view(), name='doctor-login'),
    path('dashboard/', views.DoctorDashboard.as_view(), name='doctor-dashboard'),

    path('patient_examination/<int:booking_id>/', views.PatientExaminationView.as_view(), name='patient_examination'),

]


