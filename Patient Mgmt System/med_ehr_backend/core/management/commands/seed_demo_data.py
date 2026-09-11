from django.core.management.base import BaseCommand
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_config import db


USERS_COL = 'users'
PATIENTS_COL = 'patients'
DOCTORS_COL = 'doctors'
SLOTS_COL = 'appointment_slots'
CONSULTATIONS_COL = 'consultations'
PRESCRIPTIONS_COL = 'prescriptions'


DEMO_USERS = [
    {"email": "admin@medehr.com", "password": "admin123", "name": "Admin User", "role": "admin", "entity_id": ""},
    {"email": "patient@medehr.com", "password": "patient123", "name": "Patient", "role": "patient", "entity_id": "P-001"},
    {"email": "alice@medehr.com", "password": "patient123", "name": "Alice Tan", "role": "patient", "entity_id": "P-002"},
    {"email": "bob@medehr.com", "password": "patient123", "name": "Bob Lee", "role": "patient", "entity_id": "P-003"},
    {"email": "carol@medehr.com", "password": "patient123", "name": "Carol Ng", "role": "patient", "entity_id": "P-004"},
    {"email": "david@medehr.com", "password": "patient123", "name": "David Kumar", "role": "patient", "entity_id": "P-005"},
    {"email": "emma@medehr.com", "password": "patient123", "name": "Emma Wong", "role": "patient", "entity_id": "P-006"},
    {"email": "farhan@medehr.com", "password": "patient123", "name": "Farhan Ali", "role": "patient", "entity_id": "P-007"},
    {"email": "wilson@medehr.com", "password": "doctor123", "name": "Dr. Wilson", "role": "doctor", "entity_id": "D-100"},
    {"email": "sarah@medehr.com", "password": "doctor123", "name": "Dr. Sarah Lim", "role": "doctor", "entity_id": "D-101"},
    {"email": "james@medehr.com", "password": "doctor123", "name": "Dr. James Wong", "role": "doctor", "entity_id": "D-102"},
    {"email": "emily@medehr.com", "password": "doctor123", "name": "Dr. Emily Tan", "role": "doctor", "entity_id": "D-103"},
    {"email": "rachel@medehr.com", "password": "doctor123", "name": "Dr. Rachel Chu", "role": "doctor", "entity_id": "D-104"},
    {"email": "michael@medehr.com", "password": "doctor123", "name": "Dr. Michael Ho", "role": "doctor", "entity_id": "D-105"},
    {"email": "priya@medehr.com", "password": "doctor123", "name": "Dr. Priya Nair", "role": "doctor", "entity_id": "D-106"},
    {"email": "sam@medehr.com", "password": "doctor123", "name": "Dr. Sam Philip", "role": "doctor", "entity_id": "D-107"},
    {"email": "nora@medehr.com", "password": "doctor123", "name": "Dr. Nora Kim", "role": "doctor", "entity_id": "D-108"},
]

DEMO_PATIENTS = [
    {
        "patient_id": "P-001",
        "full_name": "Patient",
        "contact_number": "1234567890",
        "email_address": "patient@medehr.com",
        "date_of_birth": "1995-06-15",
        "gender": "Male",
        "blood_group": "B+",
        "address": "12 Jalan Ampang, Kuala Lumpur",
        "emergency_contact_name": "Mary",
        "emergency_contact_number": "0123456789",
    },
    {
        "patient_id": "P-002",
        "full_name": "Alice Tan",
        "contact_number": "0192345678",
        "email_address": "alice@medehr.com",
        "date_of_birth": "1990-03-22",
        "gender": "Female",
        "blood_group": "A+",
        "address": "45 Petaling Street, Kuala Lumpur",
        "emergency_contact_name": "Ben Tan",
        "emergency_contact_number": "0112345678",
    },
    {
        "patient_id": "P-003",
        "full_name": "Bob Lee",
        "contact_number": "0173456789",
        "email_address": "bob@medehr.com",
        "date_of_birth": "1985-11-08",
        "gender": "Male",
        "blood_group": "O-",
        "address": "8 Persiaran Gurney, Penang",
        "emergency_contact_name": "Sue Lee",
        "emergency_contact_number": "0163456789",
    },
    {
        "patient_id": "P-004",
        "full_name": "Carol Ng",
        "contact_number": "0164567890",
        "email_address": "carol@medehr.com",
        "date_of_birth": "1998-07-30",
        "gender": "Female",
        "blood_group": "AB+",
        "address": "23 Bukit Bintang Road, Kuala Lumpur",
        "emergency_contact_name": "Dan Ng",
        "emergency_contact_number": "0134567890",
    },
    {
        "patient_id": "P-005",
        "full_name": "David Kumar",
        "contact_number": "0185678901",
        "email_address": "david@medehr.com",
        "date_of_birth": "1980-01-17",
        "gender": "Male",
        "blood_group": "O+",
        "address": "101 Jalan Sultan Ismail, Johor Bahru",
        "emergency_contact_name": "Rani Kumar",
        "emergency_contact_number": "0155678901",
    },
    {
        "patient_id": "P-006",
        "full_name": "Emma Wong",
        "contact_number": "0126789012",
        "email_address": "emma@medehr.com",
        "date_of_birth": "2002-09-05",
        "gender": "Female",
        "blood_group": "B-",
        "address": "66 Jalan Tun Razak, Kuala Lumpur",
        "emergency_contact_name": "Kevin Wong",
        "emergency_contact_number": "0196789012",
    },
    {
        "patient_id": "P-007",
        "full_name": "Farhan Ali",
        "contact_number": "0147890123",
        "email_address": "farhan@medehr.com",
        "date_of_birth": "1976-12-11",
        "gender": "Male",
        "blood_group": "A-",
        "address": "3 Jalan Mengkudu, Ipoh",
        "emergency_contact_name": "Nadia Ali",
        "emergency_contact_number": "0177890123",
    },
]

DEMO_DOCTORS = [
    {"doctor_id": "D-100", "doctor_name": "Dr. Wilson", "specialization": "Cardiology", "email_address": "wilson@medehr.com", "status": "approved"},
    {"doctor_id": "D-101", "doctor_name": "Dr. Sarah Lim", "specialization": "Pediatrics", "email_address": "sarah@medehr.com", "status": "approved"},
    {"doctor_id": "D-102", "doctor_name": "Dr. James Wong", "specialization": "Orthopedics", "email_address": "james@medehr.com", "status": "approved"},
    {"doctor_id": "D-103", "doctor_name": "Dr. Emily Tan", "specialization": "Dermatology", "email_address": "emily@medehr.com", "status": "approved"},
    {"doctor_id": "D-104", "doctor_name": "Dr. Rachel Chu", "specialization": "Neurology", "email_address": "rachel@medehr.com", "status": "approved"},
    {"doctor_id": "D-105", "doctor_name": "Dr. Michael Ho", "specialization": "General Surgery", "email_address": "michael@medehr.com", "status": "approved"},
    {"doctor_id": "D-106", "doctor_name": "Dr. Priya Nair", "specialization": "Gynecology", "email_address": "priya@medehr.com", "status": "approved"},
    {"doctor_id": "D-107", "doctor_name": "Dr. Sam Philip", "specialization": "Cardiology", "email_address": "sam@medehr.com", "status": "pending"},
    {"doctor_id": "D-108", "doctor_name": "Dr. Nora Kim", "specialization": "Pediatrics", "email_address": "nora@medehr.com", "status": "rejected"},
]

DEMO_SLOTS = [
    {"slot_id": "SL-001", "doctor_id": "D-100", "patient_id": None, "appointment_date": "2026-09-14", "day_of_week": "Monday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-002", "doctor_id": "D-100", "patient_id": None, "appointment_date": "2026-09-14", "day_of_week": "Monday", "start_time": "10:00:00", "end_time": "11:00:00", "status": "Available"},
    {"slot_id": "SL-003", "doctor_id": "D-100", "patient_id": None, "appointment_date": "2026-09-15", "day_of_week": "Tuesday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-004", "doctor_id": "D-101", "patient_id": None, "appointment_date": "2026-09-14", "day_of_week": "Monday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-005", "doctor_id": "D-101", "patient_id": None, "appointment_date": "2026-09-16", "day_of_week": "Wednesday", "start_time": "11:00:00", "end_time": "12:00:00", "status": "Available"},
    {"slot_id": "SL-006", "doctor_id": "D-102", "patient_id": None, "appointment_date": "2026-09-15", "day_of_week": "Tuesday", "start_time": "11:00:00", "end_time": "12:00:00", "status": "Available"},
    {"slot_id": "SL-007", "doctor_id": "D-102", "patient_id": None, "appointment_date": "2026-09-17", "day_of_week": "Thursday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-008", "doctor_id": "D-103", "patient_id": None, "appointment_date": "2026-09-16", "day_of_week": "Wednesday", "start_time": "14:00:00", "end_time": "15:00:00", "status": "Available"},
    {"slot_id": "SL-009", "doctor_id": "D-103", "patient_id": None, "appointment_date": "2026-09-18", "day_of_week": "Friday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-010", "doctor_id": "D-104", "patient_id": None, "appointment_date": "2026-09-14", "day_of_week": "Monday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-011", "doctor_id": "D-104", "patient_id": None, "appointment_date": "2026-09-18", "day_of_week": "Friday", "start_time": "15:00:00", "end_time": "16:00:00", "status": "Available"},
    {"slot_id": "SL-012", "doctor_id": "D-105", "patient_id": None, "appointment_date": "2026-09-15", "day_of_week": "Tuesday", "start_time": "14:00:00", "end_time": "15:00:00", "status": "Available"},
    {"slot_id": "SL-013", "doctor_id": "D-106", "patient_id": None, "appointment_date": "2026-09-16", "day_of_week": "Wednesday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Available"},
    {"slot_id": "SL-014", "doctor_id": "D-106", "patient_id": None, "appointment_date": "2026-09-17", "day_of_week": "Thursday", "start_time": "10:00:00", "end_time": "11:00:00", "status": "Available"},
    {"slot_id": "SL-015", "doctor_id": "D-100", "patient_id": "P-002", "appointment_date": "2026-09-15", "day_of_week": "Tuesday", "start_time": "10:00:00", "end_time": "11:00:00", "status": "Booked"},
    {"slot_id": "SL-016", "doctor_id": "D-100", "patient_id": "P-003", "appointment_date": "2026-09-16", "day_of_week": "Wednesday", "start_time": "11:00:00", "end_time": "12:00:00", "status": "Booked"},
    {"slot_id": "SL-017", "doctor_id": "D-101", "patient_id": "P-004", "appointment_date": "2026-09-17", "day_of_week": "Thursday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Booked"},
    {"slot_id": "SL-018", "doctor_id": "D-103", "patient_id": "P-002", "appointment_date": "2026-09-17", "day_of_week": "Thursday", "start_time": "14:00:00", "end_time": "15:00:00", "status": "Booked"},
    {"slot_id": "SL-019", "doctor_id": "D-105", "patient_id": "P-005", "appointment_date": "2026-09-16", "day_of_week": "Wednesday", "start_time": "14:00:00", "end_time": "15:00:00", "status": "Booked"},
    {"slot_id": "SL-020", "doctor_id": "D-100", "patient_id": "P-001", "appointment_date": "2026-09-08", "day_of_week": "Tuesday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Completed", "consultation_id": "C-202609080900"},
    {"slot_id": "SL-021", "doctor_id": "D-100", "patient_id": "P-002", "appointment_date": "2026-09-09", "day_of_week": "Wednesday", "start_time": "10:00:00", "end_time": "11:00:00", "status": "Completed", "consultation_id": "C-202609091000"},
    {"slot_id": "SL-022", "doctor_id": "D-101", "patient_id": "P-003", "appointment_date": "2026-09-08", "day_of_week": "Tuesday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Completed", "consultation_id": "C-202609080901"},
    {"slot_id": "SL-023", "doctor_id": "D-102", "patient_id": "P-005", "appointment_date": "2026-09-10", "day_of_week": "Thursday", "start_time": "11:00:00", "end_time": "12:00:00", "status": "Completed", "consultation_id": "C-202609101100"},
    {"slot_id": "SL-024", "doctor_id": "D-104", "patient_id": "P-004", "appointment_date": "2026-09-10", "day_of_week": "Thursday", "start_time": "09:00:00", "end_time": "10:00:00", "status": "Completed", "consultation_id": "C-202609100900"},
]

DEMO_CONSULTATIONS = [
    {
        "consultation_id": "C-202609080900",
        "slot_id": "SL-020",
        "doctor_id": "D-100",
        "patient_id": "P-001",
        "consultation_date": "2026-09-08",
        "diagnosis": "Hypertension Management",
        "notes": "Blood pressure elevated (145/95). Advised low-sodium diet and regular exercise. Review in 4 weeks.",
    },
    {
        "consultation_id": "C-202609091000",
        "slot_id": "SL-021",
        "doctor_id": "D-100",
        "patient_id": "P-002",
        "consultation_date": "2026-09-09",
        "diagnosis": "Chest Pain Assessment",
        "notes": "Labs normal; no signs of cardiac ischemia. Anxiety-related palpitations suspected. Reassess if symptoms persist.",
    },
    {
        "consultation_id": "C-202609080901",
        "slot_id": "SL-022",
        "doctor_id": "D-101",
        "patient_id": "P-003",
        "consultation_date": "2026-09-08",
        "diagnosis": "Child Growth Check-Up",
        "notes": "Growth within normal percentile. Vaccinations up to date. Encourage balanced nutrition and outdoor activity.",
    },
    {
        "consultation_id": "C-202609101100",
        "slot_id": "SL-023",
        "doctor_id": "D-102",
        "patient_id": "P-005",
        "consultation_date": "2026-09-10",
        "diagnosis": "Knee Sprain",
        "notes": "Grade 2 medial collateral ligament sprain of left knee. R.I.C.E. protocol advised. Physiotherapy referral given.",
    },
    {
        "consultation_id": "C-202609100900",
        "slot_id": "SL-024",
        "doctor_id": "D-104",
        "patient_id": "P-004",
        "consultation_date": "2026-09-10",
        "diagnosis": "Chronic Migraine Evaluation",
        "notes": "Patient reports 2-3 migraines monthly. Trigger factors identified. Started preventive therapy; journal on symptoms.",
    },
]

DEMO_PRESCRIPTIONS = [
    {
        "prescription_id": "Rx-202609080900",
        "consultation_id": "C-202609080900",
        "patient_id": "P-001",
        "doctor_id": "D-100",
        "prescribed_date": "2026-09-08",
        "instructions": "Take with food in the morning.",
        "medications": [
            {"name": "Amlodipine", "dosage": "5mg", "frequency": "Once daily", "duration": "30 days", "notes": "For blood pressure control."},
            {"name": "Aspirin", "dosage": "75mg", "frequency": "Once daily", "duration": "30 days", "notes": "Low-dose prevention."},
        ],
    },
    {
        "prescription_id": "Rx-202609091000",
        "consultation_id": "C-202609091000",
        "patient_id": "P-002",
        "doctor_id": "D-100",
        "prescribed_date": "2026-09-09",
        "instructions": "Take as needed, up to twice a day.",
        "medications": [
            {"name": "Propranolol", "dosage": "10mg", "frequency": "As needed", "duration": "14 days", "notes": "For palpitations."},
        ],
    },
    {
        "prescription_id": "Rx-202609080901",
        "consultation_id": "C-202609080901",
        "patient_id": "P-003",
        "doctor_id": "D-101",
        "prescribed_date": "2026-09-08",
        "instructions": "Take twice daily after meals.",
        "medications": [
            {"name": "Multivitamin Syrup", "dosage": "5ml", "frequency": "Twice daily", "duration": "30 days", "notes": "For growth and nutrition."},
            {"name": "Vitamin D3", "dosage": "400 IU", "frequency": "Once daily", "duration": "30 days", "notes": "Daily supplement."},
        ],
    },
    {
        "prescription_id": "Rx-202609101100",
        "consultation_id": "C-202609101100",
        "patient_id": "P-005",
        "doctor_id": "D-102",
        "prescribed_date": "2026-09-10",
        "instructions": "Apply locally on the affected knee after ice therapy.",
        "medications": [
            {"name": "Diclofenac Gel", "dosage": "1%", "frequency": "Three times daily", "duration": "7 days", "notes": "For pain and inflammation."},
            {"name": "Paracetamol", "dosage": "500mg", "frequency": "As needed", "duration": "7 days", "notes": "For pain relief, max 6 tablets daily."},
        ],
    },
    {
        "prescription_id": "Rx-202609100900",
        "consultation_id": "C-202609100900",
        "patient_id": "P-004",
        "doctor_id": "D-104",
        "prescribed_date": "2026-09-10",
        "instructions": "Take nightly before bed.",
        "medications": [
            {"name": "Amitriptyline", "dosage": "25mg", "frequency": "Once nightly", "duration": "90 days", "notes": "Migraine prophylaxis."},
        ],
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
            for col in [USERS_COL, PATIENTS_COL, DOCTORS_COL, SLOTS_COL, CONSULTATIONS_COL, PRESCRIPTIONS_COL]:
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
            db.collection(SLOTS_COL).document(slot['slot_id']).set(slot)
            self.stdout.write(f'  Created slot: {slot["slot_id"]} {slot["day_of_week"]} {slot["start_time"]}-{slot["end_time"]} ({slot["status"]})')

        self.stdout.write('Seeding demo consultations...')
        for consultation in DEMO_CONSULTATIONS:
            db.collection(CONSULTATIONS_COL).document(consultation['consultation_id']).set(consultation)
            self.stdout.write(f'  Created consultation: {consultation["consultation_id"]} ({consultation["diagnosis"]})')

        self.stdout.write('Seeding demo prescriptions...')
        for prescription in DEMO_PRESCRIPTIONS:
            db.collection(PRESCRIPTIONS_COL).document(prescription['prescription_id']).set(prescription)
            self.stdout.write(f'  Created prescription: {prescription["prescription_id"]}')

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))