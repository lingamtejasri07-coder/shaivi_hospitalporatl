import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.http import require_POST

from .models import Doctor, Patient, Appointment, MedicalReport
from .forms import (
    AppointmentBookingForm, 
    AppointmentStatusUpdateForm, 
    MedicalReportForm, 
    DoctorForm
)


def home(request):
    """
    Main landing and Doctor list/search/filter page.
    Includes JS filtering for Cardiology, Pediatrics, Orthopedics, Neurology, etc.
    """
    selected_dept = request.GET.get('department', 'All')
    search_query = request.GET.get('q', '').strip()

    doctors = Doctor.objects.all()

    if selected_dept != 'All' and selected_dept:
        doctors = doctors.filter(department=selected_dept)

    if search_query:
        doctors = doctors.filter(
            Q(name__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(department__icontains=search_query)
        )

    # Metrics for hero counters
    stats = {
        'total_doctors': Doctor.objects.filter(active_status=True).count(),
        'total_appointments': Appointment.objects.count(),
        'departments_count': len(Doctor.DEPARTMENT_CHOICES),
        'completed_consultations': Appointment.objects.filter(status='Completed').count(),
    }

    # Department list for filter buttons
    departments = [
        {'id': 'All', 'name': 'All Specialists', 'icon': 'bi-grid'},
        {'id': 'Cardiology', 'name': 'Cardiology', 'icon': 'bi-heart-pulse'},
        {'id': 'Pediatrics', 'name': 'Pediatrics', 'icon': 'bi-emoji-smile'},
        {'id': 'Orthopedics', 'name': 'Orthopedics', 'icon': 'bi-bandaid'},
        {'id': 'Neurology', 'name': 'Neurology', 'icon': 'bi-activity'},
        {'id': 'General Medicine', 'name': 'General Medicine', 'icon': 'bi-hospital'},
    ]

    all_active_doctors = Doctor.objects.filter(active_status=True)

    context = {
        'doctors': doctors,
        'all_doctors': all_active_doctors,
        'stats': stats,
        'departments': departments,
        'selected_dept': selected_dept,
        'search_query': search_query,
    }
    return render(request, 'hospital/home.html', context)


def book_appointment(request):
    """
    Appointment booking page with patient details and interactive slot selector.
    """
    selected_doctor_id = request.GET.get('doctor')
    initial_doctor = None
    if selected_doctor_id:
        try:
            initial_doctor = Doctor.objects.get(pk=selected_doctor_id, active_status=True)
        except Doctor.DoesNotExist:
            initial_doctor = None

    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            # Extract patient details
            email = form.cleaned_data['patient_email'].lower().strip()
            name = form.cleaned_data['patient_name'].strip()
            phone = form.cleaned_data['patient_phone'].strip()
            gender = form.cleaned_data['gender']
            date_of_birth = form.cleaned_data.get('date_of_birth')
            blood_group = form.cleaned_data.get('blood_group', '')

            # Get or create patient
            patient, created = Patient.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'phone': phone,
                    'gender': gender,
                    'date_of_birth': date_of_birth,
                    'blood_group': blood_group,
                }
            )

            # Update existing patient if name/phone changed
            if not created:
                patient.name = name
                patient.phone = phone
                patient.gender = gender
                if date_of_birth:
                    patient.date_of_birth = date_of_birth
                if blood_group:
                    patient.blood_group = blood_group
                patient.save()

            # Create appointment
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = 'Pending'
            appointment.save()

            # Store recent appointment in session for fast lookup
            request.session['last_tracking_code'] = appointment.tracking_code
            request.session['patient_email'] = patient.email

            messages.success(
                request,
                f"Your appointment with {appointment.doctor.display_name} has been successfully scheduled! "
                f"Booking Tracking ID: {appointment.tracking_code}"
            )
            return redirect('hospital:appointment_confirmation', tracking_code=appointment.tracking_code)
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        initial_data = {}
        if initial_doctor:
            initial_data['doctor'] = initial_doctor
        form = AppointmentBookingForm(initial=initial_data)

    doctors = Doctor.objects.filter(active_status=True)
    today_str = timezone.localdate().strftime('%Y-%m-%d')

    context = {
        'form': form,
        'doctors': doctors,
        'selected_doctor': initial_doctor,
        'today_str': today_str,
        'time_slots': Appointment.TIME_SLOTS,
    }
    return render(request, 'hospital/book_appointment.html', context)


def appointment_confirmation(request, tracking_code):
    """
    Displays booking confirmation with tracking ID and appointment details.
    """
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'), 
        tracking_code=tracking_code
    )
    return render(request, 'hospital/appointment_confirmation.html', {'appointment': appointment})


def api_available_slots(request):
    """
    AJAX endpoint to get slot availability for a doctor on a specific date.
    Returns list of slot status: available, booked, past.
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing doctor_id or date parameter'}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id)
        apt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid doctor ID or date format'}, status=400)

    # Get already booked slots for this doctor and date (exclude Cancelled)
    booked_slots = set(
        Appointment.objects.filter(
            doctor=doctor,
            date=apt_date
        ).exclude(status='Cancelled').values_list('time_slot', flat=True)
    )

    day_name = apt_date.strftime('%A')
    available_days = [d.strip().lower() for d in doctor.available_days.split(',')]
    is_doctor_available_day = (day_name.lower() in available_days) or (len(available_days) == 0) or ('all' in available_days)

    slots_data = []
    for slot_val, slot_label in Appointment.TIME_SLOTS:
        is_booked = slot_val in booked_slots
        slots_data.append({
            'slot': slot_val,
            'label': slot_label,
            'is_booked': is_booked,
            'status': 'Booked' if is_booked else 'Available'
        })

    return JsonResponse({
        'doctor_name': doctor.display_name,
        'department': doctor.department,
        'date': date_str,
        'day_of_week': day_name,
        'is_working_day': is_doctor_available_day,
        'available_days_raw': doctor.available_days,
        'slots': slots_data,
        'booked_count': len(booked_slots),
        'available_count': len(slots_data) - len(booked_slots)
    })


def patient_dashboard(request):
    """
    Patient dashboard showing upcoming and past appointments.
    Patients can search by their email address or tracking code.
    """
    search_query = request.GET.get('identifier', '').strip()
    session_email = request.session.get('patient_email', '')

    identifier = search_query or session_email

    appointments = Appointment.objects.none()
    patient = None

    if identifier:
        # Check by email or tracking code or phone
        patient = Patient.objects.filter(
            Q(email__iexact=identifier) | Q(phone__iexact=identifier)
        ).first()

        if patient:
            appointments = Appointment.objects.filter(patient=patient).select_related('doctor')
        else:
            # Maybe it's a tracking code
            by_code = Appointment.objects.filter(tracking_code__iexact=identifier).select_related('doctor', 'patient')
            if by_code.exists():
                appointments = by_code
                patient = by_code.first().patient

    today = timezone.localdate()
    upcoming_appointments = [
        apt for apt in appointments 
        if apt.date >= today and apt.status in ['Pending', 'Confirmed']
    ]
    past_appointments = [
        apt for apt in appointments 
        if apt.date < today or apt.status in ['Completed', 'Cancelled']
    ]

    context = {
        'identifier': identifier,
        'patient': patient,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_count': appointments.count(),
    }
    return render(request, 'hospital/patient_dashboard.html', context)


@require_POST
def cancel_appointment_patient(request, tracking_code):
    """
    Allows patient to cancel a pending appointment.
    """
    appointment = get_object_or_404(Appointment, tracking_code=tracking_code)
    if appointment.status == 'Completed':
        messages.error(request, "Completed appointments cannot be cancelled.")
    else:
        appointment.status = 'Cancelled'
        appointment.save()
        messages.success(request, f"Appointment {tracking_code} has been cancelled.")

    return redirect('hospital:patient_dashboard')


def appointment_detail(request, tracking_code):
    """
    Detailed view of an appointment, with attached medical report if available.
    """
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'),
        tracking_code=tracking_code
    )
    reports = MedicalReport.objects.filter(appointment=appointment)

    return render(request, 'hospital/appointment_detail.html', {
        'appointment': appointment,
        'reports': reports,
    })


def view_medical_report(request, report_id):
    """
    Detailed consultation/medical report page.
    """
    report = get_object_or_404(
        MedicalReport.objects.select_related('patient', 'doctor', 'appointment'),
        pk=report_id
    )
    return render(request, 'hospital/medical_report_detail.html', {'report': report})


# ==============================================================================
# ADMIN / STAFF WORKFLOW VIEWS
# ==============================================================================

def staff_login_view(request):
    """Staff authentication view."""
    if request.user.is_authenticated:
        return redirect('hospital:staff_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('hospital:staff_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'hospital/staff_login.html', {'form': form})


def staff_logout_view(request):
    """Staff logout."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('hospital:home')


@login_required
def staff_dashboard(request):
    """
    Admin/staff appointment status management portal.
    Includes filtering, inline status updates, schedule management, and report creation.
    """
    status_filter = request.GET.get('status', 'All')
    dept_filter = request.GET.get('department', 'All')
    doctor_filter = request.GET.get('doctor', 'All')
    search_q = request.GET.get('q', '').strip()
    date_filter = request.GET.get('date', '').strip()

    appointments = Appointment.objects.select_related('doctor', 'patient').order_by('-date', 'time_slot')

    if status_filter != 'All' and status_filter:
        appointments = appointments.filter(status=status_filter)

    if dept_filter != 'All' and dept_filter:
        appointments = appointments.filter(doctor__department=dept_filter)

    if doctor_filter != 'All' and doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)

    if date_filter:
        appointments = appointments.filter(date=date_filter)

    if search_q:
        appointments = appointments.filter(
            Q(tracking_code__icontains=search_q) |
            Q(patient__name__icontains=search_q) |
            Q(patient__email__icontains=search_q) |
            Q(doctor__name__icontains=search_q)
        )

    # Key staff metrics
    counts = {
        'total': Appointment.objects.count(),
        'pending': Appointment.objects.filter(status='Pending').count(),
        'confirmed': Appointment.objects.filter(status='Confirmed').count(),
        'completed': Appointment.objects.filter(status='Completed').count(),
        'cancelled': Appointment.objects.filter(status='Cancelled').count(),
        'today_count': Appointment.objects.filter(date=timezone.localdate()).count(),
    }

    doctors = Doctor.objects.all()

    context = {
        'appointments': appointments,
        'counts': counts,
        'doctors': doctors,
        'status_filter': status_filter,
        'dept_filter': dept_filter,
        'doctor_filter': doctor_filter,
        'date_filter': date_filter,
        'search_q': search_q,
        'status_choices': Appointment.STATUS_CHOICES,
        'departments': Doctor.DEPARTMENT_CHOICES,
    }
    return render(request, 'hospital/staff_dashboard.html', context)


@login_required
@require_POST
def staff_update_status(request, appointment_id):
    """
    Quick status update endpoint for admin/staff.
    """
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    new_status = request.POST.get('status')
    admin_notes = request.POST.get('admin_notes', '')

    if new_status in dict(Appointment.STATUS_CHOICES):
        appointment.status = new_status
        if admin_notes:
            appointment.admin_notes = admin_notes
        appointment.save()
        messages.success(
            request, 
            f"Appointment {appointment.tracking_code} status updated to {new_status}."
        )
    else:
        messages.error(request, "Invalid status choice selected.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'hospital:staff_dashboard'
    return redirect(next_url)


@login_required
def staff_create_medical_report(request, appointment_id):
    """
    Create medical report for an appointment and automatically mark appointment as Completed.
    """
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor'), 
        pk=appointment_id
    )

    # Check if report already exists
    existing_report = MedicalReport.objects.filter(appointment=appointment).first()

    if request.method == 'POST':
        form = MedicalReportForm(request.POST, instance=existing_report)
        if form.is_valid():
            report = form.save(commit=False)
            report.appointment = appointment
            report.patient = appointment.patient
            report.doctor = appointment.doctor
            report.save()

            # Mark appointment as completed
            if appointment.status != 'Completed':
                appointment.status = 'Completed'
                appointment.save()

            messages.success(request, f"Medical consultation report saved for {appointment.patient.name}!")
            return redirect('hospital:staff_dashboard')
    else:
        form = MedicalReportForm(instance=existing_report)

    context = {
        'form': form,
        'appointment': appointment,
        'existing_report': existing_report,
    }
    return render(request, 'hospital/medical_report_form.html', context)


@login_required
def staff_manage_doctors(request):
    """
    Staff page to view doctors, add new doctor, or toggle active status.
    """
    doctors = Doctor.objects.all().order_by('department', 'name')

    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f"Dr. {doctor.name} added successfully!")
            return redirect('hospital:staff_manage_doctors')
        else:
            messages.error(request, "Please check the form inputs.")
    else:
        form = DoctorForm()

    return render(request, 'hospital/staff_manage_doctors.html', {
        'doctors': doctors,
        'form': form,
    })


@login_required
@require_POST
def staff_toggle_doctor_status(request, doctor_id):
    """
    Toggles a doctor's active status.
    """
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    doctor.active_status = not doctor.active_status
    doctor.save()
    status_str = "Active" if doctor.active_status else "Inactive"
    messages.info(request, f"Dr. {doctor.name} is now marked as {status_str}.")
    return redirect('hospital:staff_manage_doctors')
