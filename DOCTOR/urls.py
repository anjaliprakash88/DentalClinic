from django.urls import path
from .import views

urlpatterns = [
    path('login/', views.DoctorLoginView.as_view(), name='doctor-login'),
    path('dashboard/', views.DoctorDashboard.as_view(), name='doctor-dashboard'),

]


