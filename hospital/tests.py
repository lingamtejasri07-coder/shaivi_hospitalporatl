from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Doctor, Patient, Appointment, MedicalReport
from .forms import AppointmentBookingForm


class HospitalPortalTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.localdate()
        self.tomorrow = self.today + timedelta(days=1)

        # Create doctor
        self.doctor = Doctor.objects.create(
            name="Sarah Jenkins",
            department="Cardiology",
            specialization="Interventional Cardiologist",
            consultation_fee=75.00,
            available_days="Monday, Wednesday, Friday",
            active_status=True,
            room_number="Suite 302"
        )

        # Create patient
        self.patient = Patient.objects.create(
            name="John Doe",
            email="john@example.com",
            phone="1234567890",
            gender="Male"
        )

        # Create staff user
        self.staff_user = User.objects.create_user(
            username="testadmin",
            password="testpassword",
            is_staff=True
        )

    def test_doctor_creation_and_attributes(self):
        self.assertEqual(str(self.doctor), "Dr. Sarah Jenkins - Interventional Cardiologist (Cardiology)")
        self.assertEqual(self.doctor.display_name, "Dr. Sarah Jenkins")
        self.assertEqual(self.doctor.department_badge_class, "badge-cardio")

    def test_appointment_creation_and_tracking_code(self):
        apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="10:00 AM - 10:30 AM",
            reason="Chest pain"
        )
        self.assertTrue(apt.tracking_code.startswith("APT-"))
        self.assertEqual(apt.status, "Pending")
        self.assertEqual(apt.status_badge_class, "badge-pending")

    def test_prevent_double_booking_model_validation(self):
        # Create first appointment
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="10:00 AM - 10:30 AM",
            reason="Checkup 1"
        )

        # Attempt to create overlapping appointment for same doctor, date and slot
        patient2 = Patient.objects.create(
            name="Jane Smith",
            email="jane@example.com",
            phone="9876543210"
        )
        duplicate_apt = Appointment(
            patient=patient2,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="10:00 AM - 10:30 AM",
            reason="Checkup 2"
        )
        with self.assertRaises(ValidationError):
            duplicate_apt.clean()

    def test_booking_form_validation_and_double_booking(self):
        # Existing booking
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="09:00 AM - 09:30 AM",
            reason="First Booking"
        )

        form_data = {
            'patient_name': 'Alice Bob',
            'patient_email': 'alice@example.com',
            'patient_phone': '5551234',
            'gender': 'Female',
            'doctor': self.doctor.id,
            'date': self.tomorrow,
            'time_slot': '09:00 AM - 09:30 AM', # duplicate slot
            'reason': 'Second Booking Attempt'
        }
        form = AppointmentBookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("already booked", str(form.errors))

    def test_past_date_validation(self):
        yesterday = self.today - timedelta(days=1)
        apt = Appointment(
            patient=self.patient,
            doctor=self.doctor,
            date=yesterday,
            time_slot="10:00 AM - 10:30 AM",
            reason="Past visit"
        )
        with self.assertRaises(ValidationError):
            apt.clean()

    def test_api_available_slots(self):
        # Book a slot
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="09:00 AM - 09:30 AM",
            reason="Booked slot test"
        )

        url = reverse('hospital:api_available_slots')
        response = self.client.get(url, {
            'doctor_id': self.doctor.id,
            'date': self.tomorrow.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['booked_count'], 1)
        
        # Check slot 09:00 AM - 09:30 AM is marked is_booked: True
        slot_0900 = next(s for s in data['slots'] if s['slot'] == "09:00 AM - 09:30 AM")
        self.assertTrue(slot_0900['is_booked'])

        # Check other slot is not booked
        slot_1000 = next(s for s in data['slots'] if s['slot'] == "10:00 AM - 10:30 AM")
        self.assertFalse(slot_1000['is_booked'])

    def test_medical_report_creation(self):
        apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.tomorrow,
            time_slot="11:00 AM - 11:30 AM",
            reason="Hypertension follow-up",
            status="Completed"
        )
        report = MedicalReport.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment=apt,
            diagnosis="Stage 1 Essential Hypertension",
            treatment_plan="Amlodipine 5mg once daily",
            notes="Reduce sodium intake and monitor blood pressure weekly."
        )
        self.assertEqual(report.patient, self.patient)
        self.assertEqual(report.appointment, apt)
        self.assertIn("Amlodipine", report.treatment_plan)

    def test_staff_dashboard_and_workflow(self):
        self.client.login(username="testadmin", password="testpassword")
        response = self.client.get(reverse('hospital:staff_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appointments Management Dashboard")
