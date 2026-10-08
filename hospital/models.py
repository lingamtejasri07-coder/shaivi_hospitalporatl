import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User


class Doctor(models.Model):
    DEPARTMENT_CHOICES = [
        ('Cardiology', 'Cardiology'),
        ('Pediatrics', 'Pediatrics'),
        ('Orthopedics', 'Orthopedics'),
        ('Neurology', 'Neurology'),
        ('General Medicine', 'General Medicine'),
        ('Dermatology', 'Dermatology'),
    ]

    name = models.CharField(max_length=150)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    specialization = models.CharField(max_length=200)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    available_days = models.CharField(
        max_length=200, 
        help_text="e.g. Monday, Wednesday, Friday"
    )
    active_status = models.BooleanField(default=True, verbose_name="Active Status")
    qualification = models.CharField(max_length=150, default="MBBS, MD")
    experience_years = models.PositiveIntegerField(default=8)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25, blank=True)
    room_number = models.CharField(max_length=50, default="Room 102")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization} ({self.department})"

    @property
    def display_name(self):
        if self.name.startswith("Dr."):
            return self.name
        return f"Dr. {self.name}"

    @property
    def department_badge_class(self):
        mapping = {
            'Cardiology': 'badge-cardio',
            'Pediatrics': 'badge-pediatrics',
            'Orthopedics': 'badge-ortho',
            'Neurology': 'badge-neuro',
            'General Medicine': 'badge-general',
            'Dermatology': 'badge-derma',
        }
        return mapping.get(self.department, 'badge-secondary')


class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    BLOOD_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_profile'
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_CHOICES, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=25, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"


class Appointment(models.Model):
    TIME_SLOTS = [
        ('09:00 AM - 09:30 AM', '09:00 AM - 09:30 AM'),
        ('09:30 AM - 10:00 AM', '09:30 AM - 10:00 AM'),
        ('10:00 AM - 10:30 AM', '10:00 AM - 10:30 AM'),
        ('10:30 AM - 11:00 AM', '10:30 AM - 11:00 AM'),
        ('11:00 AM - 11:30 AM', '11:00 AM - 11:30 AM'),
        ('11:30 AM - 12:00 PM', '11:30 AM - 12:00 PM'),
        ('02:00 PM - 02:30 PM', '02:00 PM - 02:30 PM'),
        ('02:30 PM - 03:00 PM', '02:30 PM - 03:00 PM'),
        ('03:00 PM - 03:30 PM', '03:00 PM - 03:30 PM'),
        ('03:30 PM - 04:00 PM', '03:30 PM - 04:00 PM'),
        ('04:00 PM - 04:30 PM', '04:00 PM - 04:30 PM'),
        ('04:30 PM - 05:00 PM', '04:30 PM - 05:00 PM'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time_slot = models.CharField(max_length=30, choices=TIME_SLOTS)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    tracking_code = models.CharField(max_length=20, unique=True, editable=False)
    admin_notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time_slot']
        unique_together = [['doctor', 'date', 'time_slot']]

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = 'APT-' + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def clean(self):
        # Prevent appointment in the past (only for new appointments)
        if self.date and self.date < timezone.localdate():
            raise ValidationError({'date': "Appointment date cannot be in the past."})

        # Prevent double booking for the same doctor, date and time slot
        if self.doctor_id and self.date and self.time_slot:
            overlapping = Appointment.objects.filter(
                doctor=self.doctor,
                date=self.date,
                time_slot=self.time_slot
            ).exclude(status='Cancelled')

            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError({
                    'time_slot': f"Dr. {self.doctor.name} is already booked for {self.time_slot} on {self.date}. Please select another time slot."
                })

    def __str__(self):
        return f"{self.tracking_code} | {self.patient.name} with {self.doctor.display_name} on {self.date} ({self.status})"

    @property
    def status_badge_class(self):
        mapping = {
            'Pending': 'badge-pending',
            'Confirmed': 'badge-confirmed',
            'Completed': 'badge-completed',
            'Cancelled': 'badge-cancelled',
        }
        return mapping.get(self.status, 'bg-secondary')

    @property
    def is_upcoming(self):
        today = timezone.localdate()
        return self.date >= today and self.status in ['Pending', 'Confirmed']


class MedicalReport(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_reports')
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_reports'
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_reports')
    diagnosis = models.TextField()
    treatment_plan = models.TextField(help_text="Prescription, recommended therapies or medicines")
    notes = models.TextField(blank=True, help_text="Additional observations or lifestyle advice")
    follow_up_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Report #{self.id} for {self.patient.name} by {self.doctor.display_name} ({self.created_date.strftime('%Y-%m-%d')})"
