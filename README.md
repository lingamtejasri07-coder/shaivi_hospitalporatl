# MediCare — Hospital & Patient Appointment Management Portal
**Django Full-Stack Capstone Project 1**

---

## 1. Project Overview
MediCare is a full-stack, responsive hospital portal developed using Django, SQLite, Bootstrap 5, and JavaScript. The system enables patients to discover specialists across medical departments, reserve consultation time slots with zero risk of double booking, track visit statuses, and access medical consultation reports. Administrative staff and doctors have a dedicated management portal to confirm or cancel visits, manage schedules, and issue digital consultation diagnoses.

---

## 2. Technology Stack
- **Backend**: Python 3.10+ / 3.11+, Django 5.x / 6.x (MVT Architecture, ORM, ModelForms)
- **Database**: SQLite (`db.sqlite3` with Django ORM)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Production Server & Static Files**: Gunicorn 21+, WhiteNoise 6.6+
- **Cloud Deployment**: Render (`render.yaml` Blueprint specification)

---

## 3. Database Architecture (Django ORM Models)

| Model | Key Fields | Description |
|---|---|---|
| **Doctor** | `name`, `department`, `specialization`, `consultation_fee`, `available_days`, `qualification`, `experience_years`, `room_number`, `active_status` | Medical specialists categorized by department (Cardiology, Pediatrics, Orthopedics, Neurology, General Medicine, Dermatology). |
| **Patient** | `name`, `email`, `phone`, `gender`, `date_of_birth`, `blood_group`, `address`, `emergency_contact` | Patient profile records linked to appointment bookings. |
| **Appointment** | `patient` (FK), `doctor` (FK), `date`, `time_slot`, `reason`, `status`, `tracking_code`, `admin_notes` | Consultation bookings with statuses: `Pending`, `Confirmed`, `Completed`, `Cancelled`. Unique constraint and clean validation prevent double booking. |
| **MedicalReport** | `patient` (FK), `doctor` (FK), `appointment` (FK), `diagnosis`, `treatment_plan`, `notes`, `follow_up_date` | Electronic medical consultation summaries and prescriptions. |

---

## 4. Key Functional Features

1. **Doctor Browsing & Instant Department Filtering**:
   - Filter specialists dynamically via JavaScript by **Cardiology**, **Pediatrics**, **Orthopedics**, **Neurology**, and **All**.
   - Real-time search across physician names and subspecialties.
   - Doctor credentials modal and consulting fees.

2. **Interactive Slot Selector & Double-Booking Prevention**:
   - Real-time slot status inspection (`/api/slots/?doctor_id=...&date=...`).
   - Automatically marks booked slots as locked/disabled with strikethrough styling.
   - Prevents booking for past dates.
   - Server-side and model-level double booking validation.

3. **Patient Portal & Tracking**:
   - Unique tracking code generated for every visit (e.g., `APT-94821`).
   - Search by email or reference code.
   - Tabbed view for **Upcoming Appointments** vs **Past & Consulted**.
   - One-click cancellation for pending visits.
   - Access to digital medical prescriptions and printable appointment slips.

4. **Staff & Admin Management Workflow**:
   - Status transitions (`Pending` &rarr; `Confirmed` &rarr; `Completed` / `Cancelled`).
   - Modal for inline status updates with administrative notes.
   - Consultation report filing (automatically sets appointment status to `Completed`).
   - Doctor roster control (activate/deactivate doctors with a single click).
   - Standard Django administration panel at `/admin/`.

---

## 5. Project Directory Structure
```
shaivisree/
├── manage.py
├── requirements.txt
├── render.yaml
├── create_superuser.py
├── db.sqlite3
├── .gitignore
├── README.md
├── mysite/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hospital/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/main.js
│   └── templates/hospital/
│       ├── base.html
│       ├── home.html
│       ├── book_appointment.html
│       ├── appointment_confirmation.html
│       ├── patient_dashboard.html
│       ├── appointment_detail.html
│       ├── medical_report_detail.html
│       ├── medical_report_form.html
│       ├── staff_login.html
│       ├── staff_dashboard.html
│       └── staff_manage_doctors.html
└── staticfiles/
```

---

## 6. Local Setup & Execution

### Step 1: Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Database Migrations & Initial Seeding
```bash
python manage.py migrate
python create_superuser.py
```
*`create_superuser.py` automatically initializes an administrator account (`admin` / `admin123`) and populates sample doctors across all 4 mandatory departments along with sample appointments.*

### Step 4: Run the Development Server
```bash
python manage.py runserver
```
Visit:
- **Public Portal**: `http://127.0.0.1:8000/`
- **Book Appointment**: `http://127.0.0.1:8000/book/`
- **Patient Dashboard**: `http://127.0.0.1:8000/dashboard/`
- **Staff Portal**: `http://127.0.0.1:8000/staff/login/` (Username: `admin`, Password: `admin123`)
- **Django Admin**: `http://127.0.0.1:8000/admin/`

### Step 5: Run Automated Unit Tests
```bash
python manage.py test hospital
```

---

## 7. Render Deployment Guide

### Deployment Configuration (`render.yaml`)
The project includes a ready-to-use Render Blueprint:
```yaml
services:
  - type: web
    name: hospital-appointment-portal-demo
    runtime: python
    rootDir: .
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py"
    startCommand: "python manage.py migrate && python create_superuser.py && gunicorn mysite.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: WEB_CONCURRENCY
        value: 2
```

### Steps to Deploy:
1. **Push Repository to GitHub**:
   ```bash
   git add .
   git commit -m "Complete Django Hospital Portal for Render"
   git push origin main
   ```
2. **Log into Render**:
   - Go to [render.com](https://render.com) and click **New + &rarr; Blueprint** (or **New + &rarr; Web Service**).
   - Connect your GitHub repository.
3. **Environment Settings**:
   - If using Web Service directly:
     - **Root Directory**: `.`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py`
     - **Start Command**: `python manage.py migrate && python create_superuser.py && gunicorn mysite.wsgi:application`
   - Add environment variables:
     - `SECRET_KEY`: `<generate-a-strong-random-key>`
     - `RENDER`: `True`
4. **Deploy**:
   - Click **Create Web Service**.
   - Render will build the environment, collect static assets via WhiteNoise, execute migrations, and seed sample data through `create_superuser.py`.
5. **Verify**:
   - Access the generated `https://<service-name>.onrender.com` URL.
   - Log into `/staff/login/` or `/admin/` with username `admin` and password `admin123`.
