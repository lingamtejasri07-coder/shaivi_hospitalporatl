from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    # Patient & Public Routes
    path('', views.home, name='home'),
    path('doctors/', views.home, name='doctor_list'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('confirmation/<str:tracking_code>/', views.appointment_confirmation, name='appointment_confirmation'),
    path('appointment/<str:tracking_code>/', views.appointment_detail, name='appointment_detail'),
    path('cancel/<str:tracking_code>/', views.cancel_appointment_patient, name='cancel_appointment'),
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('report/<int:report_id>/', views.view_medical_report, name='view_medical_report'),

    # Interactive AJAX Endpoint
    path('api/slots/', views.api_available_slots, name='api_available_slots'),

    # Staff / Admin Portal Routes
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/logout/', views.staff_logout_view, name='staff_logout'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/update-status/<int:appointment_id>/', views.staff_update_status, name='staff_update_status'),
    path('staff/appointment/<int:appointment_id>/report/', views.staff_create_medical_report, name='staff_create_medical_report'),
    path('staff/doctors/', views.staff_manage_doctors, name='staff_manage_doctors'),
    path('staff/doctors/<int:doctor_id>/toggle/', views.staff_toggle_doctor_status, name='staff_toggle_doctor'),
]
