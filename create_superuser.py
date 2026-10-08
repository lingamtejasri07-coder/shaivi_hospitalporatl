import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from hospital.models import Doctor, Patient, Appointment, MedicalReport


def setup_admin():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@medicare.local')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser created successfully: {username} / {password}")
    else:
        print(f"Superuser '{username}' already exists.")


def seed_sample_data():
    if Doctor.objects.count() >= 6:
        print("Sample data already present. Skipping seeding.")
        return

    print("Seeding initial hospital data...")

    doctors_data = [
        {
            'name': 'Sarah Jenkins',
            'department': 'Cardiology',
            'specialization': 'Interventional Cardiologist',
            'consultation_fee': 75.00,
            'available_days': 'Monday, Wednesday, Friday',
            'qualification': 'MD, FACC, Harvard Medical School',
            'experience_years': 14,
            'room_number': 'Suite 302 (Heart Center)',
            'bio': 'Specializing in heart disease prevention, coronary interventions, echocardiography, and hypertension management.',
            'email': 's.jenkins@medicare.local',
            'phone': '+1 (555) 432-8901',
            'active_status': True,
        },
        {
            'name': 'David Chen',
            'department': 'Cardiology',
            'specialization': 'Electrophysiologist & Arrhythmia Specialist',
            'consultation_fee': 80.00,
            'available_days': 'Tuesday, Thursday, Saturday',
            'qualification': 'MD, Johns Hopkins Medicine',
            'experience_years': 11,
            'room_number': 'Suite 305 (Heart Center)',
            'bio': 'Expert in cardiac rhythm disorders, pacemaker management, and non-invasive cardiovascular screening.',
            'email': 'd.chen@medicare.local',
            'phone': '+1 (555) 432-8902',
            'active_status': True,
        },
        {
            'name': 'Elena Rostova',
            'department': 'Pediatrics',
            'specialization': 'Pediatric Care & Child Development',
            'consultation_fee': 60.00,
            'available_days': 'Monday, Tuesday, Thursday, Friday',
            'qualification': 'MD, FAAP, Stanford Children\'s Health',
            'experience_years': 9,
            'room_number': 'Room 108 (Children\'s Wing)',
            'bio': 'Dedicated to compassionate infant and adolescent wellness, developmental milestones, and routine immunization.',
            'email': 'e.rostova@medicare.local',
            'phone': '+1 (555) 543-9012',
            'active_status': True,
        },
        {
            'name': 'Marcus Vance',
            'department': 'Orthopedics',
            'specialization': 'Joint Replacement & Sports Medicine',
            'consultation_fee': 85.00,
            'available_days': 'Monday, Wednesday, Thursday',
            'qualification': 'MS, FRCS Orth, Columbia University',
            'experience_years': 16,
            'room_number': 'Suite 210 (Orthopedic Care)',
            'bio': 'Pioneering minimally invasive arthroscopic surgeries, cartilage restoration, and knee & hip joint reconstruction.',
            'email': 'm.vance@medicare.local',
            'phone': '+1 (555) 654-0123',
            'active_status': True,
        },
        {
            'name': 'Amara Okafor',
            'department': 'Neurology',
            'specialization': 'Clinical Neurologist & Neurophysiology',
            'consultation_fee': 90.00,
            'available_days': 'Tuesday, Wednesday, Friday',
            'qualification': 'MD, PhD, Oxford University Hospitals',
            'experience_years': 13,
            'room_number': 'Suite 404 (Neuroscience Pavilion)',
            'bio': 'Focusing on complex headache management, neuromuscular disorders, stroke rehabilitation, and epilepsy diagnostics.',
            'email': 'a.okafor@medicare.local',
            'phone': '+1 (555) 765-1234',
            'active_status': True,
        },
        {
            'name': 'Rachel Green',
            'department': 'General Medicine',
            'specialization': 'Primary Care & Internal Medicine',
            'consultation_fee': 50.00,
            'available_days': 'Monday, Tuesday, Wednesday, Thursday, Friday',
            'qualification': 'MD, Internal Medicine, Yale Medicine',
            'experience_years': 8,
            'room_number': 'Room 101 (Outpatient Clinic)',
            'bio': 'Comprehensive general physical checkups, diabetic health, preventive medicine, and acute condition management.',
            'email': 'r.green@medicare.local',
            'phone': '+1 (555) 876-2345',
            'active_status': True,
        },
        {
            'name': 'Julian Vance',
            'department': 'Dermatology',
            'specialization': 'Clinical & Cosmetic Dermatology',
            'consultation_fee': 65.00,
            'available_days': 'Monday, Wednesday, Saturday',
            'qualification': 'MD, Board Certified Dermatologist',
            'experience_years': 10,
            'room_number': 'Suite 115 (Derm Clinic)',
            'bio': 'Specialist in skin cancer screening, chronic dermatitis, psoriasis therapy, and advanced dermatologic care.',
            'email': 'j.vance@medicare.local',
            'phone': '+1 (555) 987-3456',
            'active_status': True,
        },
    ]

    created_doctors = []
    for d_data in doctors_data:
        doc, _ = Doctor.objects.get_or_create(
            name=d_data['name'],
            defaults=d_data
        )
        created_doctors.append(doc)

    # Patients
    patients_data = [
        {
            'name': 'Emma Watson',
            'email': 'emma.watson@example.com',
            'phone': '+1 (555) 111-2233',
            'gender': 'Female',
            'date_of_birth': '1992-04-15',
            'blood_group': 'O+',
            'address': '742 Evergreen Terrace, Springfield',
        },
        {
            'name': 'James Miller',
            'email': 'james.miller@example.com',
            'phone': '+1 (555) 222-3344',
            'gender': 'Male',
            'date_of_birth': '1985-08-20',
            'blood_group': 'A+',
            'address': '124 Conch Street, Boston',
        },
        {
            'name': 'Sophia Patel',
            'email': 'sophia.patel@example.com',
            'phone': '+1 (555) 333-4455',
            'gender': 'Female',
            'date_of_birth': '2016-11-03',
            'blood_group': 'B+',
            'address': '55 Maple Avenue, Chicago',
        },
        {
            'name': 'Robert Taylor',
            'email': 'robert.taylor@example.com',
            'phone': '+1 (555) 444-5566',
            'gender': 'Male',
            'date_of_birth': '1970-02-12',
            'blood_group': 'AB+',
            'address': '890 Oak Street, Seattle',
        },
    ]

    created_patients = []
    for p_data in patients_data:
        pat, _ = Patient.objects.get_or_create(
            email=p_data['email'],
            defaults=p_data
        )
        created_patients.append(pat)

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    last_week = today - timedelta(days=7)

    # Appointments with various statuses: Pending, Confirmed, Completed, Cancelled
    appointments_seed = [
        {
            'patient': created_patients[0],
            'doctor': created_doctors[0], # Dr. Sarah Jenkins (Cardiology)
            'date': tomorrow,
            'time_slot': '10:00 AM - 10:30 AM',
            'reason': 'Experiencing mild palpitations and requesting routine cardiovascular checkup.',
            'status': 'Confirmed',
            'admin_notes': 'Confirmed via front desk. Patient asked to bring prior ECG reports.',
        },
        {
            'patient': created_patients[1],
            'doctor': created_doctors[3], # Dr. Marcus Vance (Orthopedics)
            'date': day_after,
            'time_slot': '02:00 PM - 02:30 PM',
            'reason': 'Right knee pain after sports workout; difficulty walking down stairs.',
            'status': 'Pending',
            'admin_notes': 'Awaiting confirmation of insurance authorization.',
        },
        {
            'patient': created_patients[2],
            'doctor': created_doctors[2], # Dr. Elena Rostova (Pediatrics)
            'date': today + timedelta(days=3),
            'time_slot': '09:00 AM - 09:30 AM',
            'reason': 'Routine pediatric growth milestone examination and flu vaccine booster.',
            'status': 'Confirmed',
            'admin_notes': 'Guardian confirmed appointment time.',
        },
        {
            'patient': created_patients[3],
            'doctor': created_doctors[4], # Dr. Amara Okafor (Neurology)
            'date': last_week,
            'time_slot': '11:00 AM - 11:30 AM',
            'reason': 'Chronic migraine assessment and visual aura consultations.',
            'status': 'Completed',
            'admin_notes': 'Consultation completed. MRI ordered and prescription provided.',
        },
        {
            'patient': created_patients[0],
            'doctor': created_doctors[5], # Dr. Rachel Green (General Med)
            'date': today + timedelta(days=5),
            'time_slot': '03:00 PM - 03:30 PM',
            'reason': 'Annual health physical and routine blood panel review.',
            'status': 'Cancelled',
            'admin_notes': 'Cancelled by patient due to work travel rescheduling.',
        },
    ]

    for apt_data in appointments_seed:
        apt, created = Appointment.objects.get_or_create(
            doctor=apt_data['doctor'],
            date=apt_data['date'],
            time_slot=apt_data['time_slot'],
            defaults=apt_data
        )

        # Create medical report for completed appointment
        if apt.status == 'Completed':
            MedicalReport.objects.get_or_create(
                appointment=apt,
                defaults={
                    'patient': apt.patient,
                    'doctor': apt.doctor,
                    'diagnosis': 'Migraine with aura; episodic tension-type headache.',
                    'treatment_plan': '1. Sumatriptan 50mg as needed at aura onset.\n2. Magnesium Glycinate 400mg daily supplement.\n3. Keep headache trigger diary for 4 weeks.',
                    'notes': 'Patient reports high work stress and irregular sleep. Recommended progressive relaxation exercises and regular hydration.',
                    'follow_up_date': today + timedelta(days=21),
                }
            )

    print("Sample hospital data created successfully!")


if __name__ == '__main__':
    setup_admin()
    seed_sample_data()
