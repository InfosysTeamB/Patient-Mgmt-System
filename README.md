# Med-EHR - Patient Management System

A full-stack web application providing a unified portal for **patients**, **doctors**, and **admins** to manage profiles, appointments, consultations, and prescriptions. Features role-based access with three distinct portals, each with tailored views and capabilities.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Firebase Configuration](#firebase-configuration)
- [Authentication](#authentication)
  - [Demo Accounts](#demo-accounts)
  - [How Auth Works](#how-auth-works)
- [User Roles & Portals](#user-roles--portals)
  - [Admin Portal](#admin-portal)
  - [Patient Portal](#patient-portal)
  - [Doctor Portal](#doctor-portal)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Component Reference](#component-reference)
- [Configuration](#configuration)
- [Known Limitations](#known-limitations)
- [Dependencies](#dependencies)
- [License](#license)

---

## Features

- **Role-Based Access Control** - Three distinct portals (Admin, Patient, Doctor) with route guards and separate navigation
- **Patient Management** - Full CRUD operations for patient records (create, read, update, delete)
- **Doctor Management** - Full CRUD operations for doctor profiles with specialization tracking
- **Appointment Scheduling** - Create, book, view, complete, and cancel appointment slots
- **Weekly Schedule Grid** - Visual weekly timetable showing slot availability across weekdays
- **Consultations** - Doctors can record consultations with diagnosis and notes when completing appointments
- **Prescriptions** - Doctors can prescribe medications linked to consultations
- **Treatment History** - Patients and doctors can view chronological treatment history (consultations + prescriptions)
- **Self-Registration** - Users can register accounts as patients or doctors; admins are pre-seeded
- **Search & Filter** - Client-side search across patients, doctors, and appointment records
- **Profile Management** - Patients and doctors can view and edit their own profiles
- **Availability Management** - Doctors can add and manage their available time slots
- **Overview Dashboards** - Role-specific overview pages with quick stats
- **Toast Notifications** - Non-intrusive success/error/info feedback
- **Confirm Dialogs** - Confirmation prompts for destructive actions
- **Loading Spinners** - Visual loading indicators during async operations
- **Responsive Sidebar Navigation** - Themed sidebars with role-specific color schemes

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|-------------------------------------------------|
| Frontend    | Angular 16, TypeScript 5.0, RxJS 7.8            |
| Backend     | Django 5.2+, Django REST Framework 3.15         |
| Database    | Google Cloud Firestore (primary), SQLite (Django internals) |
| Auth        | Custom token-based auth (Firestore tokens, localStorage persistence) |
| CORS        | django-cors-headers (allow all origins)         |
| Styling     | Plain CSS with CSS custom properties (design tokens) |
| Testing     | Jasmine 4.6 + Karma 6.4 (frontend)              |

---

## Project Structure

```
Patient Mgmt System/
├── README.md
├── requirements.txt                    # Python dependencies
├── SETUP_GUIDE.txt                     # Team setup instructions
│
├── med_ehr_backend/                    # Django REST API Backend
│   ├── manage.py                       # Django management script
│   ├── firebase_config.py             # Firebase/Firestore initialization
│   ├── serviceAccountKey.json         # Firebase service account credentials
│   ├── db.sqlite3                     # SQLite (Django internals only)
│   ├── med_ehr_backend/               # Django project config
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── core/                          # Main Django app
│       ├── models.py                  # Dataclass models (Patient, Doctor, Appointment, Consultation, Prescription)
│       ├── serializers.py            # DRF serializers
│       ├── views.py                  # API viewsets + auth views
│       ├── urls.py                   # API URL routing
│       ├── auth.py                   # Firebase token authentication backend
│       ├── permissions.py            # Role-based permission classes
│       ├── admin.py
│       ├── apps.py
│       └── management/commands/
│           └── seed_demo_data.py     # Management command to seed demo data
│
└── med-ehr-frontend/                   # Angular 16 Frontend
    ├── package.json
    ├── angular.json
    ├── tsconfig.json
    └── src/
        ├── index.html
        ├── main.ts
        ├── styles.css                 # Global styles (design tokens)
        └── app/
            ├── app.module.ts          # Root module
            ├── app-routing.module.ts  # Route definitions
            ├── interceptors/
            │   └── auth.interceptor.ts    # Attaches auth token to HTTP requests
            ├── guards/
            │   ├── auth.guard.ts          # Redirects unauthenticated users to login
            │   └── role.guard.ts          # Restricts routes to specific roles
            ├── services/
            │   ├── api.service.ts         # HTTP API client
            │   ├── auth.service.ts        # Auth state (localStorage persistence)
            │   ├── toast.service.ts       # Toast notification service
            │   └── confirm.service.ts     # Confirmation dialog service
            └── components/
                ├── role-selector/              # Login/Register page
                ├── shared/
                │   ├── toast-container/        # Toast notification display
                │   ├── confirm-dialog/         # Confirmation dialog overlay
                │   └── loading-spinner/        # Loading spinner component
                ├── admin-dashboard/            # Admin shell with sidebar
                ├── admin-overview/             # Admin: overview/dashboard
                ├── admin-patients/             # Admin: patient CRUD
                ├── admin-doctors/              # Admin: doctor CRUD
                ├── admin-appointments/         # Admin: appointment slot CRUD
                ├── patient-portal/             # Patient shell with sidebar
                ├── patient-overview/           # Patient: overview/dashboard
                ├── patient-profile/            # Patient: view/edit profile
                ├── patient-book/               # Patient: book appointments
                ├── patient-appointments/       # Patient: view/cancel bookings
                ├── patient-doctors/            # Patient: browse doctors
                ├── patient-treatment-history/  # Patient: view treatment history
                ├── patient-prescriptions/      # Patient: view prescriptions
                ├── doctor-portal/              # Doctor shell with sidebar
                ├── doctor-overview/            # Doctor: overview/dashboard
                ├── doctor-profile/             # Doctor: view/edit profile
                ├── doctor-schedule/            # Doctor: manage availability grid
                ├── doctor-appointments/        # Doctor: view booked appointments
                ├── doctor-consultations/       # Doctor: manage consultations
                ├── doctor-prescriptions/       # Doctor: manage prescriptions
                ├── patient-registration/       # (Legacy, not routed)
                ├── doctor-registration/        # (Legacy, not routed)
                └── appointment-booking/        # (Legacy, not routed)
```

---

## Prerequisites

- **Python** 3.13+
- **Node.js** 16+ and npm
- **Git**
- **Google Cloud Firestore** project (Firebase project: `med-ehr`)

---

## Installation

### Backend Setup

```bash
# Navigate to the project directory
cd "Patient Mgmt System"

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the backend server (starts at http://127.0.0.1:8000)
cd med_ehr_backend
python manage.py runserver
```

### Frontend Setup (separate terminal)

```bash
# Navigate to the frontend directory
cd "Patient Mgmt System/med-ehr-frontend"

# Install dependencies
npm install

# Run the frontend dev server (starts at http://localhost:4200)
npm start
```

### Running Both

The backend runs on `http://127.0.0.1:8000` and the frontend on `http://localhost:4200`. Open two separate terminals to run both simultaneously. The Angular dev server proxies `/api/*` requests to the backend via `proxy.conf.json`, so no CORS issues occur during development.

### Seeding Demo Data (optional)

```bash
cd med_ehr_backend
python manage.py seed_demo_data
```

Creates the demo accounts, patient, doctors, and appointment slots listed below.

---

## Firebase Configuration

The backend uses **Google Cloud Firestore** as its primary database through the Firebase Admin SDK.

- **Project ID:** `med-ehr`
- **Service Account:** `firebase-adminsdk-fbsvc@med-ehr.iam.gserviceaccount.com`
- **Config file:** `med_ehr_backend/serviceAccountKey.json`
- **Initialization:** `firebase_config.py` loads the service account and initializes the Firestore client

### Firestore Collections

| Collection           | Description                              |
|----------------------|------------------------------------------|
| `users`              | User accounts (email, password, role)    |
| `patients`           | Patient profile records                  |
| `doctors`            | Doctor profile records                   |
| `appointment_slots`  | Appointment time slots                   |
| `consultations`      | Completed consultation records           |
| `prescriptions`      | Medication prescriptions                 |
| `tokens`             | Auth tokens (opaque, stored server-side) |

---

## Authentication

### Demo Accounts

Pre-seeded in Firestore via `python manage.py seed_demo_data`:

| Role    | Email                 | Password     |
|---------|-----------------------|--------------|
| Admin   | admin@medehr.com      | admin123     |
| Patient | patient@medehr.com    | patient123   |
| Doctor  | wilson@medehr.com     | doctor123    |
| Doctor  | sarah@medehr.com      | doctor123    |
| Doctor  | james@medehr.com      | doctor123    |
| Doctor  | emily@medehr.com      | doctor123    |

### How Auth Works

1. **Login** (`POST /api/auth/login/`): Accepts email/password, queries Firestore `users` collection, performs plaintext password comparison, generates an opaque token stored in the `tokens` collection, and returns user details (token, id, email, name, role, entity_id)
2. **Registration** (`POST /api/auth/register/`): Creates a new user record in Firestore. For patient/doctor roles, auto-generates a unique `entity_id` (e.g., `P-20260904123456`) and creates a corresponding profile record. Returns a token immediately.
3. **Frontend Auth State**: The token and user object are persisted to `localStorage` via `AuthService`. An `AuthInterceptor` automatically attaches the `Authorization: Token <token>` header to all API requests.
4. **Route Guards**: `AuthGuard` redirects unauthenticated users to the login page. `RoleGuard` restricts portal routes to the appropriate role (e.g., only admins can access `/admin/*`).
5. **Logout** (`POST /api/auth/logout/`): Deletes the token from Firestore and clears `localStorage`.
6. **Session**: Auth state persists across page refreshes via `localStorage`. A 401 response from the backend triggers automatic logout and redirect to the login screen.

---

## User Roles & Portals

### Admin Portal (`/admin`)

The admin has full access to manage all entities in the system.

| Route                 | Feature                                    |
|-----------------------|--------------------------------------------|
| `/admin/overview`     | Dashboard overview with quick stats        |
| `/admin/patients`     | View, create, edit, and delete patient records |
| `/admin/doctors`      | View, create, edit, and delete doctor profiles |
| `/admin/appointments` | View, create, edit, and delete appointment slots |

**Capabilities:**
- Register new patients and doctors with auto-generated IDs
- Create appointment slots linked to specific doctors
- Inline editing of all records in data tables
- Searchable tables with client-side filtering
- Status badges for slot availability (Available / Booked / Completed)

**Theme:** Dark top navigation (`#1f2937`), dark sidebar

### Patient Portal (`/patient`)

Patients can manage their profile, book appointments, view treatment history, and browse doctors.

| Route                          | Feature                                  |
|--------------------------------|------------------------------------------|
| `/patient/overview`            | Dashboard overview with quick stats      |
| `/patient/profile`             | View and edit personal profile           |
| `/patient/book`                | Browse weekly schedule and book slots    |
| `/patient/appointments`        | View booked appointments, cancel them    |
| `/patient/doctors`             | Browse available doctors                 |
| `/patient/treatment-history`   | View chronological treatment history     |
| `/patient/prescriptions`       | View prescribed medications              |

**Capabilities:**
- View profile details (name, ID, contact, email, DOB)
- Edit profile information
- Browse weekly schedule grid showing slot statuses
- Book available appointment slots
- Cancel existing bookings
- Search doctors by name or specialization
- View treatment history (consultations + prescriptions sorted by date)
- View prescriptions with medication details

**Theme:** Green-themed top navigation (`#059669`), green sidebar

### Doctor Portal (`/doctor`)

Doctors manage their profile, availability schedule, consultations, prescriptions, and view booked appointments.

| Route                       | Feature                                  |
|-----------------------------|------------------------------------------|
| `/doctor/overview`          | Dashboard overview with quick stats      |
| `/doctor/profile`           | View and edit personal profile           |
| `/doctor/schedule`          | Manage weekly availability grid          |
| `/doctor/appointments`      | View booked appointments                 |
| `/doctor/consultations`     | Manage consultations (create, edit, delete) |
| `/doctor/prescriptions`     | Manage prescriptions (create, edit, delete) |

**Capabilities:**
- View profile details (name, ID, specialization)
- Edit profile information
- Add new availability slots (date, day, time range)
- View weekly schedule grid for own slots
- Delete available (unbooked) slots
- View list of booked appointments with patient details
- Complete consultations with diagnosis and notes (marks slot as Completed)
- Create and manage prescriptions linked to consultations
- Prescribe medications with name, dosage, frequency, duration, and notes

**Theme:** Blue-themed top navigation (`#0284c7`), blue sidebar

---

## API Endpoints

All endpoints are prefixed with `/api/`.

### Authentication

| Method | Endpoint               | Description              | Request Body                                        |
|--------|------------------------|--------------------------|----------------------------------------------------|
| POST   | `/api/auth/login/`     | Authenticate user        | `{ email, password }`                              |
| POST   | `/api/auth/register/`  | Register new user        | `{ email, password, name, role, entity_id? }`      |
| POST   | `/api/auth/logout/`    | Logout (invalidate token)| *(requires `Authorization: Token <token>` header)* |

### Patients

| Method | Endpoint               | Description          |
|--------|------------------------|----------------------|
| GET    | `/api/patients/`       | List all patients    |
| POST   | `/api/patients/`       | Create a patient     |
| GET    | `/api/patients/{id}/`  | Retrieve a patient   |
| PUT    | `/api/patients/{id}/`  | Full update          |
| PATCH  | `/api/patients/{id}/`  | Partial update       |
| DELETE | `/api/patients/{id}/`  | Delete a patient     |

### Doctors

| Method | Endpoint              | Description         |
|--------|-----------------------|---------------------|
| GET    | `/api/doctors/`       | List all doctors    |
| POST   | `/api/doctors/`       | Create a doctor     |
| GET    | `/api/doctors/{id}/`  | Retrieve a doctor   |
| PUT    | `/api/doctors/{id}/`  | Full update         |
| PATCH  | `/api/doctors/{id}/`  | Partial update      |
| DELETE | `/api/doctors/{id}/`  | Delete a doctor     |

### Appointment Slots

| Method | Endpoint             | Description                              |
|--------|----------------------|------------------------------------------|
| GET    | `/api/slots/`        | List all slots (with resolved details)   |
| POST   | `/api/slots/`        | Create a new slot                        |
| GET    | `/api/slots/{id}/`   | Retrieve a slot                          |
| PUT    | `/api/slots/{id}/`   | Full update                              |
| PATCH  | `/api/slots/{id}/`   | Partial update (booking/canceling/completing) |
| DELETE | `/api/slots/{id}/`   | Delete a slot                            |

### Consultations

| Method | Endpoint                    | Description                              |
|--------|-----------------------------|------------------------------------------|
| GET    | `/api/consultations/`       | List consultations (filtered by role)    |
| POST   | `/api/consultations/`       | Create a consultation                    |
| GET    | `/api/consultations/{id}/`  | Retrieve a consultation                  |
| PUT    | `/api/consultations/{id}/`  | Full update                              |
| DELETE | `/api/consultations/{id}/`  | Delete a consultation                    |

### Prescriptions

| Method | Endpoint                    | Description                              |
|--------|-----------------------------|------------------------------------------|
| GET    | `/api/prescriptions/`       | List prescriptions (filtered by role)    |
| POST   | `/api/prescriptions/`       | Create a prescription                    |
| GET    | `/api/prescriptions/{id}/`  | Retrieve a prescription                  |
| PUT    | `/api/prescriptions/{id}/`  | Full update                              |
| DELETE | `/api/prescriptions/{id}/`  | Delete a prescription                    |

### Treatment History

| Method | Endpoint                                  | Description                              |
|--------|-------------------------------------------|------------------------------------------|
| GET    | `/api/treatment-history/{patient_id}/`    | Chronological list of consultations + prescriptions for a patient |

---

## Database Schema

### `users` Collection

| Field       | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| `email`     | string | User email (login identifier)                  |
| `password`  | string | Password (stored in plaintext)                 |
| `name`      | string | User's display name                            |
| `role`      | string | One of: `admin`, `patient`, `doctor`           |
| `entity_id`| string | Links to patient/doctor profile (empty for admin) |

### `patients` Collection

| Field            | Type   | Description                               |
|------------------|--------|-------------------------------------------|
| `patient_id`     | string | Document ID (e.g., `P-001`, `P-YYYYMMDDHHmmss`) |
| `full_name`      | string | Patient's full name                       |
| `contact_number` | string | Phone number                              |
| `email_address`  | string | Email address                             |
| `date_of_birth`  | string | ISO format `YYYY-MM-DD`                  |

### `doctors` Collection

| Field           | Type   | Description                               |
|-----------------|--------|-------------------------------------------|
| `doctor_id`     | string | Document ID (e.g., `D-100`, `D-YYYYMMDDHHmmss`) |
| `doctor_name`   | string | Doctor's name                             |
| `specialization`| string | Medical specialization                    |
| `email_address` | string | Doctor's email (optional, used for admin-created logins) |

### `appointment_slots` Collection

| Field              | Type         | Description                               |
|--------------------|--------------|-------------------------------------------|
| `slot_id`          | string       | Auto-generated Firestore document ID      |
| `doctor_id`        | string       | References a doctor's `doctor_id`         |
| `patient_id`       | string/null  | References a patient's `patient_id` (null if available) |
| `appointment_date` | string/null  | ISO date `YYYY-MM-DD`                    |
| `day_of_week`      | string       | e.g., `Monday`, `Tuesday`                |
| `start_time`       | string       | e.g., `09:00`                            |
| `end_time`         | string       | e.g., `10:00`                            |
| `status`           | string       | `"Available"` (default), `"Booked"`, or `"Completed"` |
| `consultation_id`  | string/null  | Added when a consultation is recorded    |

### `consultations` Collection

| Field             | Type   | Description                               |
|-------------------|--------|-------------------------------------------|
| `consultation_id` | string | Document ID (e.g., `C-YYYYMMDDHHMMSS`)    |
| `slot_id`         | string | References an `appointment_slots` doc     |
| `doctor_id`       | string | References a doctor's `doctor_id`         |
| `patient_id`      | string | References a patient's `patient_id`       |
| `consultation_date`| string | ISO date `YYYY-MM-DD`                    |
| `diagnosis`       | string | Diagnosis summary                         |
| `notes`           | string | Doctor's consultation notes               |

### `prescriptions` Collection

| Field            | Type   | Description                               |
|------------------|--------|-------------------------------------------|
| `prescription_id`| string | Document ID (e.g., `Rx-YYYYMMDDHHMMSS`)   |
| `consultation_id`| string | References a `consultations` doc          |
| `patient_id`     | string | References a patient's `patient_id`       |
| `doctor_id`      | string | References a doctor's `doctor_id`         |
| `medications`    | array  | List of `{ name, dosage, frequency, duration, notes }` |
| `instructions`   | string | General instructions                      |
| `prescribed_date`| string | ISO date `YYYY-MM-DD`                    |

### `tokens` Collection

| Field       | Type   | Description                               |
|-------------|--------|-------------------------------------------|
| (token)     | string | Document ID = opaque auth token           |
| `user_id`   | string | Reference to the `users` document ID      |
| `role`      | string | User's role at login time                 |
| `entity_id` | string | Links to patient/doctor profile           |

---

## Component Reference

### Core Components

| Component                    | Route                      | Description                                          |
|------------------------------|--------------------------------------------------|------------------------------------------------------|
| `RoleSelectorComponent`      | `/`                         | Landing page with split-screen login/register form   |

### Shared UI Components

| Component                    | Description                                              |
|------------------------------|----------------------------------------------------------|
| `ToastContainerComponent`    | Renders toast notifications from the `ToastService`      |
| `ConfirmDialogComponent`     | Renders confirmation prompts from the `ConfirmService`   |
| `LoadingSpinnerComponent`    | Reusable loading spinner                                 |

### Admin Components

| Component                    | Route                      | Description                                          |
|------------------------------|--------------------------------------------------|------------------------------------------------------|
| `AdminDashboardComponent`    | `/admin`                    | Shell with top nav, sidebar, and router outlet       |
| `AdminOverviewComponent`     | `/admin/overview`           | Dashboard overview with quick stats                 |
| `AdminPatientsComponent`     | `/admin/patients`           | Patient CRUD with searchable data table              |
| `AdminDoctorsComponent`      | `/admin/doctors`            | Doctor CRUD with searchable data table               |
| `AdminAppointmentsComponent` | `/admin/appointments`       | Appointment slot CRUD with status badges             |

### Patient Components

| Component                    | Route                          | Description                                          |
|------------------------------|--------------------------------|------------------------------------------------------|
| `PatientPortalComponent`     | `/patient`                     | Shell with top nav, sidebar, and router outlet       |
| `PatientOverviewComponent`   | `/patient/overview`            | Dashboard overview with quick stats                  |
| `PatientProfileComponent`    | `/patient/profile`             | View/edit personal profile                           |
| `PatientBookComponent`       | `/patient/book`                | Weekly schedule grid + booking form                  |
| `PatientAppointmentsComponent`| `/patient/appointments`       | List booked appointments with cancel option          |
| `PatientDoctorsComponent`    | `/patient/doctors`             | Browse all doctors (read-only)                       |
| `PatientTreatmentHistoryComponent` | `/patient/treatment-history` | View chronological consultations + prescriptions   |
| `PatientPrescriptionsComponent` | `/patient/prescriptions`    | View prescriptions with medication details           |

### Doctor Components

| Component                    | Route                          | Description                                          |
|------------------------------|--------------------------------|------------------------------------------------------|
| `DoctorPortalComponent`      | `/doctor`                      | Shell with top nav, sidebar, and router outlet       |
| `DoctorOverviewComponent`    | `/doctor/overview`             | Dashboard overview with quick stats                  |
| `DoctorProfileComponent`     | `/doctor/profile`              | View/edit personal profile                           |
| `DoctorScheduleComponent`    | `/doctor/schedule`             | Manage weekly availability + add/delete slots        |
| `DoctorAppointmentsComponent`| `/doctor/appointments`         | View booked appointments with patient details        |
| `DoctorConsultationsComponent` | `/doctor/consultations`      | Manage consultations (complete bookings, create/edit) |
| `DoctorPrescriptionsComponent` | `/doctor/prescriptions`      | Manage prescriptions linked to consultations         |

### Legacy Components (not routed)

| Component                    | Description                                              |
|------------------------------|----------------------------------------------------------|
| `PatientRegistrationComponent`| Standalone patient registration form (earlier iteration) |
| `DoctorRegistrationComponent` | Standalone doctor registration form (earlier iteration)  |
| `AppointmentBookingComponent` | Standalone appointment management (earlier iteration)    |

---

## Configuration

### Hardcoded Settings

| Setting                   | Value                                        | Location                    |
|---------------------------|----------------------------------------------|-----------------------------|
| Backend API URL           | `/api` (relative, proxied to `127.0.0.1:8000` via `proxy.conf.json`) | `api.service.ts` / `angular.json` |
| Django SECRET_KEY         | `django-insecure-5p5=-ck3d=...`             | `settings.py`               |
| DEBUG                     | `True`                                       | `settings.py`               |
| ALLOWED_HOSTS             | `['*']`                                      | `settings.py`               |
| CORS_ALLOW_ALL_ORIGINS    | `True`                                       | `settings.py`               |
| EMAIL_BACKEND             | Console (prints to stdout)                   | `settings.py`               |
| Firebase Project          | `med-ehr`                                    | `serviceAccountKey.json`    |
| Default Profile Password  | `medehr@123` (auto-created accounts for admin-registered patients/doctors) | `views.py` |

### Demo Data

```bash
cd med_ehr_backend
python manage.py seed_demo_data        # Seed demo users, patients, doctors, slots
python manage.py seed_demo_data --clear  # Clear existing data first, then seed
```

### Time Slot Configuration

Appointment slots can be created flexibly (any date, day, and time range chosen by the doctor/admin). The original demo seed uses slots like 09:00-13:00 on weekdays:

| Slot | Time Range  |
|------|-------------|
| 1    | 09:00-10:00 |
| 2    | 10:00-11:00 |
| 3    | 11:00-12:00 |
| 4    | 12:00-13:00 |

Weekdays only (Monday through Friday) is the demo convention; the API itself does not restrict dates or day-of-week.

### Self-Registration Defaults

When a patient or doctor self-registers through the auth form:
- Patient DOB defaults to `2000-01-01`
- Doctor specialization defaults to `"General"`

---

## Known Limitations

1. **Plaintext Passwords** - User passwords are stored and compared in plaintext in Firestore
2. **No Password Hashing** - Django's built-in password validators are bypassed by the custom auth system
3. **No Token Expiry** - Auth tokens have no expiration; they remain valid until logout
4. **Firebase Key in Repo** - `serviceAccountKey.json` with private key is committed to the repository
5. **CORS Wide Open** - `CORS_ALLOW_ALL_ORIGINS = True` allows any origin
6. **N+1 Query Pattern** - Slot/consultation/prescription listing makes separate Firestore reads for each record to resolve doctor/patient details
7. **Fixed Demo Slots** - Seed data ships with weekday-only slots in the 09:00-13:00 range
8. **Legacy Components** - Three components are declared in the module but not routed (earlier iterations)
9. **No Authorization on Lists** - All doctors and (unfiltered for admin) slots are visible to every authenticated user; filtering is done at the view level per role

---

## Dependencies

### Backend (Python)

| Package               | Version   | Purpose                              |
|-----------------------|-----------|--------------------------------------|
| Django                | >=5.2     | Web framework                        |
| djangorestframework   | >=3.15    | REST API toolkit                     |
| django-cors-headers   | >=4.3     | CORS support                         |
| firebase-admin        | >=6.5     | Firebase/Firestore admin SDK         |

### Frontend (npm)

| Package                                | Version   | Purpose                          |
|----------------------------------------|-----------|----------------------------------|
| @angular/core                          | ^16.0.0   | Angular core framework           |
| @angular/common                        | ^16.0.0   | Common Angular utilities         |
| @angular/compiler                      | ^16.0.0   | Angular template compiler        |
| @angular/forms                         | ^16.0.0   | Template-driven forms            |
| @angular/platform-browser              | ^16.0.0   | Browser platform                 |
| @angular/platform-browser-dynamic      | ^16.0.0   | Dynamic bootstrapping            |
| @angular/router                        | ^16.0.0   | Client-side routing              |
| @angular/animations                    | ^16.0.0   | Angular animations               |
| rxjs                                   | ~7.8.0    | Reactive extensions              |
| firebase                               | ^10.14.1  | Firebase JS SDK (declared)       |
| tslib                                  | ^2.3.0    | TypeScript helpers               |
| zone.js                                | ~0.13.0   | Angular zone management          |
| typescript                             | ~5.0.2    | TypeScript compiler              |
| @angular/cli                           | ~16.0.2   | Angular CLI                      |
| @angular-devkit/build-angular          | ^16.0.2   | Angular build system             |
| jasmine-core                           | ~4.6.0    | Test framework                   |
| karma                                  | ~6.4.0    | Test runner                      |
| karma-chrome-launcher                  | ~3.2.0    | Chrome test launcher             |
| karma-coverage                         | ~2.2.0    | Code coverage                    |

---

## Styling

The application uses **plain CSS** with **CSS custom properties** (design tokens) defined in `styles.css`.

### Color Themes

| Portal  | Primary Color | Usage                              |
|---------|---------------|------------------------------------|
| Admin   | `#1f2937`     | Dark gray top nav and sidebar      |
| Patient | `#059669`     | Green top nav and sidebar          |
| Doctor  | `#0284c7`     | Blue top nav and sidebar           |

### Design System Features

- CSS custom properties for consistent spacing, colors, and typography
- Box shadows and border-radius for card-based layouts
- Status badges (Available = green, Booked = red)
- Responsive sidebar navigation with icons
- Split-screen login layout with gradient branding panel

---

## Testing

### Frontend Tests

```bash
cd med-ehr-frontend
npm test       # Runs Karma + Jasmine tests
```

### Backend Tests

```bash
cd med_ehr_backend
python manage.py test
```

> Note: The `tests.py` file in the backend is currently empty.

---

## License

This project does not currently include a license file.
