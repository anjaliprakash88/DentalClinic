from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.DoctorLoginView.as_view(), name='doctor-login'),
    path('dashboard/', views.DoctorDashboard.as_view(), name='doctor-dashboard'),
    path('dentalchart/<int:booking_id>/', views.DentalExaminationView.as_view(), name="dentalchart"),
    path('paediatric_dentalchart/<int:booking_id>/', views.PaediatricDentalExaminationView.as_view(), name="dentalchart"),
    path('generalchart/<int:booking_id>/', views.GeneralExaminationAPIView.as_view(), name="generalchart"),




]


