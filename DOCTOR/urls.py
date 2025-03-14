from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.DoctorLoginView.as_view(), name='doctor-login'),
    path('dashboard/', views.DoctorDashboard.as_view(), name='doctor-dashboard'),
    path('dentalchart/<int:booking_id>/', views.DentalExaminationView.as_view(), name="dentalchart"),
    path('paediatric_dentalchart/<int:booking_id>/', views.PaediatricDentalExaminationView.as_view(), name="dentalchart"),
    path('treatment-summary/<int:booking_id>/', views.TreatmentSummaryView.as_view(), name='treatment_summary'),
    path('medicine-prescription/<int:booking_id>/', views.MedicineAPIView.as_view(), name='medicine-prescription'),

    path('treatment-bill/<int:booking_id>/', views.TreatmentBillView.as_view(), name='treatment-bill'),



    path('generalchart/<int:booking_id>/', views.GeneralExaminationAPIView.as_view(), name="generalchart"),




]


