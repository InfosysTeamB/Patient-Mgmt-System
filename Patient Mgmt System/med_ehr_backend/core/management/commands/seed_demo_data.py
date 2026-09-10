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
        "email": "muhilan@medehr.com",
        "password": "patient123",
        "name": "Muhilan",
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
]

DEMO_PATIENTS = [
    {
        "patient_id": "P-001",
        "full_name": "Muhilan",
        "contact_number": "1234567890",
        "email_address": "muhilan@medehr.com",
        "date_of_birth": "1995-06-15",
    },
]

DEMO_DOCTORS = [
    {
        "doctor_id": "D-100",
        "doctor_name": "Dr. Wilson",
        "specialization": "Cardiology",
    },
]

DEMO_SLOTS = [
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-15",
        "day_of_week": "Monday",
        "start_time": "09:00",
        "end_time": "10:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-15",
        "day_of_week": "Monday",
        "start_time": "10:00",
        "end_time": "11:00",
        "status": "Available",
    },
    {
        "doctor_id": "D-100",
        "patient_id": None,
        "appointment_date": "2026-09-16",
        "day_of_week": "Tuesday",
        "start_time": "09:00",
        "end_time": "10:00",
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
