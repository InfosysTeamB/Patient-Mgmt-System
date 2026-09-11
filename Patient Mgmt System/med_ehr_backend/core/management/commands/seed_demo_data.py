from django.core.management.base import BaseCommand
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_config import db


USERS_COL = 'users'
PATIENTS_COL = 'patients'
DOCTORS_COL = 'doctors'
SLOTS_COL = 'appointment_slots'


DEMO_USERS = [
    {
        "email": "admin@medehr.com",
        "password": "admin123",
        "name": "Admin User",
        "role": "admin",
        "entity_id": "",
    },
    {
        "email": "patient@medehr.com",
        "password": "patient123",
        "name": "Patient",
        "role": "patient",
        "entity_id": "P-001",
    },
    {
        "email": "wilson@medehr.com",
        "password": "doctor123",
        "name": "Dr. Wilson",
        "role": "doctor",
        "entity_id": "D-100",
    },
    {
        "email": "sarah@medehr.com",
        "password": "doctor123",
        "name": "Dr. Sarah Lim",
        "role": "doctor",
        "entity_id": "D-101",
    },
    {
        "email": "james@medehr.com",
        "password": "doctor123",
        "name": "Dr. James Wong",
        "role": "doctor",
        "entity_id": "D-102",
    },
    {
        "email": "emily@medehr.com",
        "password": "doctor123",
        "name": "Dr. Emily Tan",
        "role": "doctor",
        "entity_id": "D-103",
    },
]

DEMO_PATIENTS = [
    {
        "patient_id": "P-001",
        "full_name": "Patient",
        "contact_number": "1234567890",
        "email_address": "patient@medehr.com",
        "date_of_birth": "1995-06-15",
    },
]

DEMO_DOCTORS = [
    {
        "doctor_id": "D-100",
        "doctor_name": "Dr. Wilson",
        "specialization": "Cardiology",
        "email_address": "wilson@medehr.com",
    },
    {
        "doctor_id": "D-101",
        "doctor_name": "Dr. Sarah Lim",
        "specialization": "Pediatrics",
        "email_address": "sarah@medehr.com",
    },
    {
        "doctor_id": "D-102",
        "doctor_name": "Dr. James Wong",
        "specialization": "Orthopedics",
        "email_address": "james@medehr.com",
    },
    {
        "doctor_id": "D-103",
        "doctor_name": "Dr. Emily Tan",
        "specialization": "Dermatology",
        "email_address": "emily@medehr.com",
    },
]

DEMO_SLOTS = [
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-14",
        "day_of_week": "Monday",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-14",
        "day_of_week": "Monday",
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-15",
        "day_of_week": "Tuesday",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-101",
        "patient_id": None,
        "appointment_date": "2026-09-21",
        "day_of_week": "Monday",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-101",
        "patient_id": None,
        "appointment_date": "2026-09-22",
        "day_of_week": "Tuesday",
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-102",
        "patient_id": None,
        "appointment_date": "2026-09-23",
        "day_of_week": "Wednesday",
        "start_time": "11:00:00",
        "end_time": "12:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-102",
        "patient_id": None,
        "appointment_date": "2026-09-24",
        "day_of_week": "Thursday",
        "start_time": "14:00:00",
        "end_time": "15:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-103",
        "patient_id": None,
        "appointment_date": "2026-09-25",
        "day_of_week": "Friday",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-103",
        "patient_id": None,
        "appointment_date": "2026-09-25",
        "day_of_week": "Friday",
        "start_time": "15:00:00",
        "end_time": "16:00:00",
        "status": "Available",
    },
]


class Command(BaseCommand):
    help = 'Seed demo accounts and sample data into Firestore'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Clear existing demo data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            for col in [USERS_COL, PATIENTS_COL, DOCTORS_COL, SLOTS_COL]:
                docs = db.collection(col).stream()
                for doc in docs:
                    doc.reference.delete()
            self.stdout.write(self.style.WARNING('All data cleared.'))

        self.stdout.write('Seeding demo users...')
        for user in DEMO_USERS:
            existing = db.collection(USERS_COL).where(filter=FieldFilter('email', '==', user['email'])).stream()
            for doc in existing:
                doc.reference.delete()
            db.collection(USERS_COL).add(user)
            self.stdout.write(f'  Created user: {user["email"]} ({user["role"]})')

        self.stdout.write('Seeding demo patients...')
        for patient in DEMO_PATIENTS:
            db.collection(PATIENTS_COL).document(patient['patient_id']).set(patient)
            self.stdout.write(f'  Created patient: {patient["full_name"]} ({patient["patient_id"]})')

        self.stdout.write('Seeding demo doctors...')
        for doctor in DEMO_DOCTORS:
            db.collection(DOCTORS_COL).document(doctor['doctor_id']).set(doctor)
            self.stdout.write(f'  Created doctor: {doctor["doctor_name"]} ({doctor["doctor_id"]})')

        self.stdout.write('Seeding demo appointment slots...')
        for slot in DEMO_SLOTS:
            db.collection(SLOTS_COL).add(slot)
            self.stdout.write(f'  Created slot: {slot["day_of_week"]} {slot["start_time"]}-{slot["end_time"]}')

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
