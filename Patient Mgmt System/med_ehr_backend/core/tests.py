import secrets
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from google.cloud.firestore_v1 import DELETE_FIELD

import core.views as views
import core.auth as auth


# ---------------------------------------------------------------------------
# In-memory fake Firestore backend (mocks core.views.db and core.auth.db)
# ---------------------------------------------------------------------------

def _match(data, field, op, value):
    actual = data.get(field)
    if op == '==':
        return actual == value
    return True


class FakeSnapshot:
    def __init__(self, data, id=None):
        self._data = data or {}
        self.exists = data is not None
        self.id = id or secrets.token_hex(6)

    def to_dict(self):
        return dict(self._data)


class FakeDocRef:
    def __init__(self, store, col, doc_id):
        self.store = store
        self.col = col
        self.doc_id = doc_id

    def get(self):
        data = self.store[self.col].get(self.doc_id)
        return FakeSnapshot(data, id=self.doc_id)

    def set(self, data):
        self.store[self.col][self.doc_id] = dict(data)

    def update(self, data):
        existing = self.store[self.col].setdefault(self.doc_id, {})
        for k, v in data.items():
            if v is DELETE_FIELD:
                existing.pop(k, None)
            else:
                existing[k] = v

    def delete(self):
        self.store[self.col].pop(self.doc_id, None)


class FakeQuery:
    def __init__(self, docs):
        self._docs = docs

    def where(self, filter=None):
        field = filter.field_path
        op = filter.op_string
        value = filter.value
        filtered = {k: v for k, v in self._docs.items() if _match(v, field, op, value)}
        return FakeQuery(filtered)

    def stream(self):
        return (FakeSnapshot(dict(d), id=k) for k, d in self._docs.items())


class FakeCollection:
    def __init__(self, store, name):
        self.store = store
        self.name = name

    def document(self, doc_id):
        return FakeDocRef(self.store, self.name, doc_id)

    def add(self, data):
        doc_id = 'auto-' + secrets.token_hex(4)
        self.store[self.name][doc_id] = dict(data)

        class _Ref:
            def __init__(self, store, col, doc_id):
                self.store = store
                self.col = col
                self.doc_id = doc_id
            @property
            def id(self):
                return self.doc_id
        return (FakeDocRef(self.store, self.name, doc_id), _Ref(self.store, self.name, doc_id))

    def stream(self):
        return (FakeSnapshot(dict(d), id=k) for k, d in self.store[self.name].items())

    def where(self, filter=None):
        query = FakeQuery(dict(self.store[self.name]))
        if filter is not None:
            query = query.where(filter)
        return query


class FakeFirestore:
    def __init__(self):
        self.store = {
            'users': {},
            'patients': {},
            'doctors': {},
            'appointment_slots': {},
            'consultations': {},
            'prescriptions': {},
            'tokens': {},
        }

    def collection(self, name):
        return FakeCollection(self.store, name)


# ---------------------------------------------------------------------------
# Base test case that patches the real Firestore client
# ---------------------------------------------------------------------------

class FirestoreTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.fake = FakeFirestore()
        self._patches = [
            patch.object(views, 'db', self.fake),
            patch.object(auth, 'db', self.fake),
        ]
        for p in self._patches:
            p.start()
        self.addCleanup(self._stop_patches)

    def _stop_patches(self):
        for p in self._patches:
            p.stop()

    def seed_user(self, email, password, name, role, entity_id='', user_id=None):
        uid = user_id or 'user-' + secrets.token_hex(3)
        self.fake.store['users'][uid] = {
            'email': email, 'password': password, 'name': name,
            'role': role, 'entity_id': entity_id,
        }
        return uid

    def token_for(self, uid, role, entity_id=''):
        token = secrets.token_hex(16)
        self.fake.store['tokens'][token] = {
            'user_id': uid, 'role': role, 'entity_id': entity_id,
        }
        return token

    def seed_patient(self, patient_id, full_name='Test Patient'):
        self.fake.store['patients'][patient_id] = {
            'patient_id': patient_id, 'full_name': full_name,
            'contact_number': '0123456789', 'email_address': f'{patient_id}@medehr.com',
            'date_of_birth': '2000-01-01',
        }

    def seed_doctor(self, doctor_id, doctor_name='Dr Test'):
        self.fake.store['doctors'][doctor_id] = {
            'doctor_id': doctor_id, 'doctor_name': doctor_name,
            'specialization': 'General', 'email_address': '',
        }

    def seed_slot(self, slot_id, doctor_id, status='Available', patient_id=None,
                  appointment_date='2026-09-20', day_of_week='Monday',
                  start_time='09:00:00', end_time='10:00:00'):
        self.fake.store['appointment_slots'][slot_id] = {
            'doctor_id': doctor_id, 'status': status,
            'patient_id': patient_id, 'appointment_date': appointment_date,
            'day_of_week': day_of_week, 'start_time': start_time, 'end_time': end_time,
        }


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------

class AuthTests(FirestoreTestCase):

    def test_login_returns_token(self):
        self.seed_user('admin@medehr.com', 'admin123', 'Admin', 'admin')
        resp = self.client.post('/api/auth/login/', {'email': 'admin@medehr.com', 'password': 'admin123'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json())
        self.assertTrue(self.fake.store['tokens'])

    def test_register_returns_token_and_creates_profile(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'patient@test.com', 'password': 'pass123',
            'name': 'New Patient', 'role': 'patient'
        })
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertIn('token', body)
        self.assertTrue(self.fake.store['patients'])
        self.assertTrue(self.fake.store['tokens'])

    def test_register_rejects_admin_role(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'a@test.com', 'password': 'pass123', 'name': 'A', 'role': 'admin'
        })
        self.assertEqual(resp.status_code, 400)

    def test_unauthenticated_request_rejected(self):
        resp = self.client.get('/api/patients/')
        self.assertIn(resp.status_code, (401, 403))

    def test_invalid_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token not-a-real-token')
        resp = self.client.get('/api/patients/')
        self.assertEqual(resp.status_code, 401)

    def test_logout_deletes_token(self):
        uid = self.seed_user('doc@medehr.com', 'doc123', 'Doc', 'doctor')
        token = self.token_for(uid, 'doctor')
        self.assertTrue(self.fake.store['tokens'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.fake.store['tokens'])


# ---------------------------------------------------------------------------
# Role-based access control tests
# ---------------------------------------------------------------------------

class RoleAccessTests(FirestoreTestCase):

    def test_patient_cannot_create_patient(self):
        uid = self.seed_user('p@test.com', 'pw', 'P', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/patients/', {'patient_id': 'P-2', 'full_name': 'X',
                                                   'contact_number': '1', 'email_address': 'x@x.com',
                                                   'date_of_birth': '2000-01-01'})
        self.assertEqual(resp.status_code, 403)

    def test_patient_reads_only_own_patient_record(self):
        self.seed_patient('P-1', 'Patient One')
        self.seed_patient('P-2', 'Patient Two')
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp = self.client.get('/api/patients/')
        self.assertEqual(resp.status_code, 200)
        names = [p['full_name'] for p in resp.json()]
        self.assertEqual(names, ['Patient One'])

    def test_patient_cannot_update_another_patient(self):
        self.seed_patient('P-1')
        self.seed_patient('P-2')
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.put('/api/patients/P-2/', {'patient_id': 'P-2', 'full_name': 'Hacked',
                                                      'contact_number': '1', 'email_address': 'h@h.com',
                                                      'date_of_birth': '2000-01-01'})
        self.assertEqual(resp.status_code, 403)

    def test_patient_optionally_updates_own_record(self):
        self.seed_patient('P-1', 'Old Name')
        uid = self.seed_user('p1@test.com', 'pw', 'Old Name', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.put('/api/patients/P-1/', {'patient_id': 'P-1', 'full_name': 'New Name',
                                                      'contact_number': '0123456789', 'email_address': 'p1@test.com',
                                                      'date_of_birth': '2000-01-01'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['patients']['P-1']['full_name'], 'New Name')

    def test_doctor_cannot_create_doctor(self):
        uid = self.seed_user('d@test.com', 'pw', 'D', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/doctors/', {'doctor_id': 'D-2', 'doctor_name': 'X', 'specialization': 'Gen'})
        self.assertEqual(resp.status_code, 403)

    def test_doctor_reads_patients(self):
        self.seed_patient('P-1', 'Patient One')
        uid = self.seed_user('d@test.com', 'pw', 'D', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/patients/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)


# ---------------------------------------------------------------------------
# Slot booking / completion consistency tests
# ---------------------------------------------------------------------------

class SlotConsistencyTests(FirestoreTestCase):

    def test_cannot_book_already_booked_slot(self):
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-9')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Booked'})
        self.assertEqual(resp.status_code, 400)

    def test_patient_books_available_slot(self):
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.seed_slot('S-1', 'D-1', status='Available')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Booked'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['patient_id'], 'P-1')
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['status'], 'Booked')

    def test_doctor_cannot_complete_others_slot(self):
        self.seed_doctor('D-1')
        self.seed_doctor('D-2')
        self.seed_patient('P-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.seed_slot('S-1', 'D-2', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'diagnosis': 'Flu', 'notes': ''}
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_completes_own_slot_creates_consultation(self):
        self.seed_doctor('D-1')
        self.seed_patient('P-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'diagnosis': 'Influenza', 'notes': 'Rest and fluids'}
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['status'], 'Completed')
        self.assertTrue(self.fake.store['consultations'])
        consultation = list(self.fake.store['consultations'].values())[0]
        self.assertEqual(consultation['diagnosis'], 'Influenza')
        self.assertEqual(consultation['patient_id'], 'P-1')

    def test_completing_available_slot_rejected(self):
        self.seed_doctor('D-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.seed_slot('S-1', 'D-1', status='Available')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'diagnosis': 'Flu'}
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_completion_requires_diagnosis(self):
        self.seed_doctor('D-1')
        self.seed_patient('P-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'notes': 'No diagnosis here'}
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(self.fake.store['consultations'])


# ---------------------------------------------------------------------------
# Prescription rules
# ---------------------------------------------------------------------------

class PrescriptionTests(FirestoreTestCase):

    def _seed_consultation(self, consultation_id='C-1', doctor_id='D-1', patient_id='P-1'):
        self.fake.store['consultations'][consultation_id] = {
            'consultation_id': consultation_id, 'slot_id': 'S-1',
            'doctor_id': doctor_id, 'patient_id': patient_id,
            'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }

    def test_create_prescription_requires_valid_consultation(self):
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-NOPE', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-09-20',
            'medications': [{'name': 'Paracetamol', 'dosage': '500mg', 'frequency': '3x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_doctor_prescription_linked_to_own_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-2', patient_id='P-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-09-20',
            'medications': [{'name': 'Paracetamol', 'dosage': '500mg', 'frequency': '3x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_creates_prescription_for_own_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-1', patient_id='P-1')
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-09-20',
            'medications': [{'name': 'Paracetamol', 'dosage': '500mg', 'frequency': '3x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(self.fake.store['prescriptions'])


# ---------------------------------------------------------------------------
# Treatment history access rules
# ---------------------------------------------------------------------------

class TreatmentHistoryTests(FirestoreTestCase):

    def _seed_history(self, patient_id, consultation_id):
        self.fake.store['consultations'][consultation_id] = {
            'consultation_id': consultation_id, 'slot_id': 'S-1',
            'doctor_id': 'D-1', 'patient_id': patient_id,
            'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }
        rx_id = 'Rx-' + consultation_id
        self.fake.store['prescriptions'][rx_id] = {
            'prescription_id': rx_id, 'consultation_id': consultation_id,
            'patient_id': patient_id, 'doctor_id': 'D-1',
            'medications': [{'name': 'Paracetamol', 'dosage': '500mg', 'frequency': '3x/day'}],
            'instructions': '', 'prescribed_date': '2026-09-20',
        }
        self.fake.store['prescriptions'][rx_id]['prescription_id'] = rx_id

    def test_patient_sees_own_history(self):
        self._seed_history('P-1', 'C-1')
        self._seed_history('P-2', 'C-2')
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_patient_cannot_read_other_history(self):
        self._seed_history('P-2', 'C-2')
        uid = self.seed_user('p1@test.com', 'pw', 'P1', 'patient', 'P-1')
        token = self.token_for(uid, 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/treatment-history/P-2/')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_sees_only_own_patients_history(self):
        self.fake.store['consultations']['C-1'] = {
            'consultation_id': 'C-1', 'slot_id': 'S-1', 'doctor_id': 'D-1',
            'patient_id': 'P-1', 'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }
        uid = self.seed_user('d1@test.com', 'pw', 'D1', 'doctor', 'D-1')
        token = self.token_for(uid, 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)


# =========================================================================
#  COMPREHENSIVE WEBSITE FEATURE TESTS
#  Covers every endpoint and user flow visible in the Med-EHR website
# =========================================================================


class AuthComprehensiveTests(FirestoreTestCase):

    def test_login_with_wrong_password(self):
        self.seed_user('admin@medehr.com', 'admin123', 'Admin', 'admin')
        resp = self.client.post('/api/auth/login/', {'email': 'admin@medehr.com', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 401)

    def test_login_unknown_email(self):
        resp = self.client.post('/api/auth/login/', {'email': 'ghost@medehr.com', 'password': 'pass'})
        self.assertEqual(resp.status_code, 401)

    def test_login_missing_fields(self):
        resp = self.client.post('/api/auth/login/', {'email': 'a@b.com'})
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post('/api/auth/login/', {'password': 'pass'})
        self.assertEqual(resp.status_code, 400)

    def test_register_returns_201_with_entity_id_for_patient(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'pat@test.com', 'password': 'pw', 'name': 'Pat', 'role': 'patient'
        })
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertTrue(body['entity_id'].startswith('P-'))
        self.assertIn('patients', self.fake.store)
        self.assertTrue(self.fake.store['patients'])

    def test_register_returns_201_with_entity_id_for_doctor(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'doc@test.com', 'password': 'pw', 'name': 'Doc', 'role': 'doctor'
        })
        self.assertEqual(resp.status_code, 201)
        body = resp.json()
        self.assertTrue(body['entity_id'].startswith('D-'))
        self.assertTrue(self.fake.store['doctors'])

    def test_register_invalid_role(self):
        resp = self.client.post('/api/auth/register/', {
            'email': 'x@test.com', 'password': 'pw', 'role': 'nurse'
        })
        self.assertEqual(resp.status_code, 400)

    def test_register_missing_fields(self):
        resp = self.client.post('/api/auth/register/', {'email': 'x@test.com'})
        self.assertEqual(resp.status_code, 400)

    def test_register_duplicate_email(self):
        self.seed_user('dup@test.com', 'pw', 'Dup', 'patient')
        resp = self.client.post('/api/auth/register/', {
            'email': 'dup@test.com', 'password': 'pw', 'name': 'Dup2', 'role': 'patient'
        })
        self.assertEqual(resp.status_code, 400)

    def test_logout_with_no_auth_header(self):
        resp = self.client.post('/api/auth/logout/')
        self.assertIn(resp.status_code, (400, 401))

    def test_login_all_roles(self):
        for role in ('admin', 'patient', 'doctor'):
            self.seed_user(f'{role}@medehr.com', 'pw', role, role)
            resp = self.client.post('/api/auth/login/', {'email': f'{role}@medehr.com', 'password': 'pw'})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()['role'], role)

    def test_login_response_has_expected_fields(self):
        uid = self.seed_user('admin@medehr.com', 'admin123', 'Admin', 'admin')
        resp = self.client.post('/api/auth/login/', {'email': 'admin@medehr.com', 'password': 'admin123'})
        body = resp.json()
        for key in ('token', 'id', 'email', 'name', 'role', 'entity_id'):
            self.assertIn(key, body)


# ---------------------------------------------------------------------------
#  Admin Patient Management
# ---------------------------------------------------------------------------

class AdminPatientTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def test_admin_creates_patient(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/patients/', {
            'patient_id': 'P-NEW', 'full_name': 'New Patient',
            'contact_number': '123', 'email_address': 'new@medehr.com',
            'date_of_birth': '1990-01-01',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()['login_created'])

    def test_admin_creates_patient_no_email(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/patients/', {
            'patient_id': 'P-NOE', 'full_name': 'No Email',
            'contact_number': '123', 'email_address': '',
            'date_of_birth': '1990-01-01',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_admin_duplicate_patient_id(self):
        self.seed_patient('P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/patients/', {
            'patient_id': 'P-1', 'full_name': 'Dup',
            'contact_number': '123', 'email_address': 'd@d.com',
            'date_of_birth': '2000-01-01',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_admin_lists_all_patients(self):
        self.seed_patient('P-1', 'A')
        self.seed_patient('P-2', 'B')
        self.seed_patient('P-3', 'C')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/patients/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)

    def test_admin_retrieves_patient(self):
        self.seed_patient('P-1', 'Retrieve Me')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/patients/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['full_name'], 'Retrieve Me')

    def test_admin_retrieve_nonexistent_patient(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/patients/P-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_admin_full_updates_patient(self):
        self.seed_patient('P-1', 'Old')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.put('/api/patients/P-1/', {
            'patient_id': 'P-1', 'full_name': 'New',
            'contact_number': '999', 'email_address': 'n@n.com',
            'date_of_birth': '1985-06-15',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['patients']['P-1']['full_name'], 'New')

    def test_admin_patches_patient(self):
        self.seed_patient('P-1', 'Original')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.patch('/api/patients/P-1/', {'full_name': 'Patched'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['patients']['P-1']['full_name'], 'Patched')

    def test_admin_deletes_patient(self):
        self.seed_patient('P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.delete('/api/patients/P-1/')
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('P-1', self.fake.store['patients'])

    def test_admin_delete_nonexistent_patient(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.delete('/api/patients/P-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_doctor_cannot_create_patient(self):
        uid = self.seed_user('d@medehr.com', 'pw', 'D', 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "doctor", "D-1")}')
        resp = self.client.post('/api/patients/', {
            'patient_id': 'P-X', 'full_name': 'X', 'contact_number': '1',
            'email_address': 'x@x.com', 'date_of_birth': '2000-01-01',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_cannot_delete_patient(self):
        self.seed_patient('P-1')
        uid = self.seed_user('d@medehr.com', 'pw', 'D', 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "doctor", "D-1")}')
        resp = self.client.delete('/api/patients/P-1/')
        self.assertEqual(resp.status_code, 403)

    def test_patient_retrieves_own_record(self):
        self.seed_patient('P-1', 'My Record')
        uid = self.seed_user('p@medehr.com', 'pw', 'P', 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "patient", "P-1")}')
        resp = self.client.get('/api/patients/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['full_name'], 'My Record')

    def test_patient_retrieve_other_record_forbidden(self):
        self.seed_patient('P-2', 'Other')
        uid = self.seed_user('p@medehr.com', 'pw', 'P', 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "patient", "P-1")}')
        resp = self.client.get('/api/patients/P-2/')
        self.assertEqual(resp.status_code, 403)


# ---------------------------------------------------------------------------
#  Admin Doctor Management
# ---------------------------------------------------------------------------

class AdminDoctorTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def test_admin_creates_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/doctors/', {
            'doctor_id': 'D-NEW', 'doctor_name': 'Dr New',
            'specialization': 'Cardiology', 'email_address': 'docnew@medehr.com',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()['login_created'])

    def test_admin_creates_doctor_blank_email_no_login(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/doctors/', {
            'doctor_id': 'D-NOE', 'doctor_name': 'Dr No Email',
            'specialization': 'Gen', 'email_address': '',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.json()['login_created'])

    def test_admin_duplicate_doctor_id(self):
        self.seed_doctor('D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/doctors/', {
            'doctor_id': 'D-1', 'doctor_name': 'Dup',
            'specialization': 'Gen', 'email_address': 'd@d.com',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_admin_lists_all_doctors(self):
        self.seed_doctor('D-1', 'Dr A')
        self.seed_doctor('D-2', 'Dr B')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/doctors/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_admin_retrieves_doctor(self):
        self.seed_doctor('D-1', 'Dr Retrieve')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/doctors/D-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['doctor_name'], 'Dr Retrieve')

    def test_admin_retrieve_nonexistent_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/doctors/D-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_admin_full_updates_doctor(self):
        self.seed_doctor('D-1', 'Dr Old')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.put('/api/doctors/D-1/', {
            'doctor_id': 'D-1', 'doctor_name': 'Dr New',
            'specialization': 'Neurology', 'email_address': 'n@n.com',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['doctors']['D-1']['doctor_name'], 'Dr New')

    def test_admin_patches_doctor(self):
        self.seed_doctor('D-1', 'Dr Original')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.patch('/api/doctors/D-1/', {'doctor_name': 'Dr Patched'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['doctors']['D-1']['doctor_name'], 'Dr Patched')

    def test_admin_deletes_doctor(self):
        self.seed_doctor('D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.delete('/api/doctors/D-1/')
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('D-1', self.fake.store['doctors'])

    def test_admin_delete_nonexistent_doctor(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.delete('/api/doctors/D-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_patient_cannot_create_doctor(self):
        uid = self.seed_user('p@medehr.com', 'pw', 'P', 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "patient", "P-1")}')
        resp = self.client.post('/api/doctors/', {
            'doctor_id': 'D-X', 'doctor_name': 'X', 'specialization': 'X',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_updates_own_profile(self):
        uid = self.seed_user('d@medehr.com', 'pw', 'D', 'doctor', 'D-1')
        self.seed_doctor('D-1', 'Dr Old')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "doctor", "D-1")}')
        resp = self.client.put('/api/doctors/D-1/', {
            'doctor_id': 'D-1', 'doctor_name': 'Dr Updated',
            'specialization': 'Oncology', 'email_address': '',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['doctors']['D-1']['doctor_name'], 'Dr Updated')

    def test_doctor_cannot_update_other_doctor(self):
        uid = self.seed_user('d@medehr.com', 'pw', 'D', 'doctor', 'D-1')
        self.seed_doctor('D-2', 'Dr Other')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "doctor", "D-1")}')
        resp = self.client.put('/api/doctors/D-2/', {
            'doctor_id': 'D-2', 'doctor_name': 'Hacked',
            'specialization': 'Gen', 'email_address': '',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_cannot_delete_doctor(self):
        self.seed_doctor('D-1')
        uid = self.seed_user('d@medehr.com', 'pw', 'D', 'doctor', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "doctor", "D-1")}')
        resp = self.client.delete('/api/doctors/D-1/')
        self.assertEqual(resp.status_code, 403)

    def test_patient_reads_all_doctors(self):
        self.seed_doctor('D-1', 'Dr A')
        self.seed_doctor('D-2', 'Dr B')
        uid = self.seed_user('p@medehr.com', 'pw', 'P', 'patient', 'P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "patient", "P-1")}')
        resp = self.client.get('/api/doctors/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)


# ---------------------------------------------------------------------------
#  Appointment Slot Lifecycle (admin + doctor + patient)
# ---------------------------------------------------------------------------

class SlotManagementTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def _doctor_token(self, doctor_id='D-1'):
        uid = self.seed_user(f'd@{doctor_id}.com', 'pw', 'Dr', 'doctor', doctor_id)
        return self.token_for(uid, 'doctor', doctor_id)

    def _patient_token(self, patient_id='P-1'):
        uid = self.seed_user(f'p@{patient_id}.com', 'pw', 'Pat', 'patient', patient_id)
        return self.token_for(uid, 'patient', patient_id)

    def test_admin_creates_slot(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Monday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
            'appointment_date': '2026-10-01', 'status': 'Available',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['status'], 'Available')

    def test_doctor_creates_slot_forced_doctor_id(self):
        self.seed_doctor('D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-WRONG', 'day_of_week': 'Monday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        created_id = resp.json()['id']
        self.assertEqual(self.fake.store['appointment_slots'][created_id]['doctor_id'], 'D-1')

    def test_patient_cannot_create_slot(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token()}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Monday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_admin_lists_all_slots(self):
        self.seed_slot('S-1', 'D-1')
        self.seed_slot('S-2', 'D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/slots/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_admin_retrieves_slot_with_details(self):
        self.seed_doctor('D-1', 'Dr Alice')
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/slots/S-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['doctor_details']['doctor_name'], 'Dr Alice')

    def test_admin_full_updates_slot(self):
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.put('/api/slots/S-1/', {
            'doctor_id': 'D-1', 'day_of_week': 'Tuesday',
            'start_time': '10:00:00', 'end_time': '11:00:00',
            'status': 'Available',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['day_of_week'], 'Tuesday')

    def test_doctor_edits_own_slot(self):
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/slots/S-1/', {
            'doctor_id': 'D-1', 'day_of_week': 'Friday',
            'start_time': '11:00:00', 'end_time': '12:00:00',
            'status': 'Available',
        }, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_doctor_cannot_edit_other_slot(self):
        self.seed_slot('S-1', 'D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/slots/S-1/', {
            'doctor_id': 'D-2', 'day_of_week': 'Monday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
            'status': 'Available',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_admin_deletes_slot(self):
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.delete('/api/slots/S-1/')
        self.assertEqual(resp.status_code, 204)

    def test_doctor_deletes_own_slot(self):
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/slots/S-1/')
        self.assertEqual(resp.status_code, 204)

    def test_doctor_cannot_delete_other_slot(self):
        self.seed_slot('S-1', 'D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/slots/S-1/')
        self.assertEqual(resp.status_code, 403)

    def test_patient_can_delete_slot(self):
        self.seed_slot('S-1', 'D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token()}')
        resp = self.client.delete('/api/slots/S-1/')
        self.assertEqual(resp.status_code, 204)

    def test_patient_cannot_book_other_patients_slot(self):
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-9')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_doctor_cannot_book(self):
        self.seed_slot('S-1', 'D-1', status='Available')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_patient_cancel_own_booking(self):
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Available', 'patient_id': '',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        slot = self.fake.store['appointment_slots']['S-1']
        self.assertEqual(slot['status'], 'Available')

    def test_patient_cancel_other_booking_forbidden(self):
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-9')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Available'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_patient_cancel_not_booked_slot(self):
        self.seed_slot('S-1', 'D-1', status='Available')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Available'}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_patient_cannot_complete_slot(self):
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'diagnosis': 'Flu'},
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_admin_completes_slot(self):
        self.seed_slot('S-1', 'D-1', status='Booked', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.patch('/api/slots/S-1/', {
            'status': 'Completed', 'consultation': {'diagnosis': 'Cold', 'notes': 'Mild'},
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['status'], 'Completed')
        self.assertTrue(self.fake.store['consultations'])

    def test_patient_rebook_completed_slot(self):
        self.seed_slot('S-1', 'D-1', status='Completed', patient_id='P-1')
        self.seed_doctor('D-1')
        self.seed_patient('P-2')
        uid = self.seed_user('p2@medehr.com', 'pw', 'P2', 'patient', 'P-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_for(uid, "patient", "P-2")}')
        resp = self.client.patch('/api/slots/S-1/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots']['S-1']['patient_id'], 'P-2')

    def test_slot_not_found_partial_update(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.patch('/api/slots/S-NONE/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_slot_not_found_retrieve(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/slots/S-NONE/')
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
#  Consultation Management
# ---------------------------------------------------------------------------

class ConsultationManagementTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def _doctor_token(self, doctor_id='D-1'):
        uid = self.seed_user(f'd@{doctor_id}.com', 'pw', 'Dr', 'doctor', doctor_id)
        return self.token_for(uid, 'doctor', doctor_id)

    def _patient_token(self, patient_id='P-1'):
        uid = self.seed_user(f'p@{patient_id}.com', 'pw', 'Pat', 'patient', patient_id)
        return self.token_for(uid, 'patient', patient_id)

    def _seed_consultation(self, cid='C-1', doctor_id='D-1', patient_id='P-1'):
        self.fake.store['consultations'][cid] = {
            'consultation_id': cid, 'slot_id': 'S-1',
            'doctor_id': doctor_id, 'patient_id': patient_id,
            'consultation_date': '2026-09-20', 'notes': 'test', 'diagnosis': 'Flu',
        }

    def test_doctor_creates_consultation(self):
        self.seed_doctor('D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/consultations/', {
            'slot_id': 'S-1', 'doctor_id': 'D-WRONG', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'Cold',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        cid = resp.json()['id']
        self.assertTrue(cid.startswith('C-'))
        self.assertEqual(self.fake.store['consultations'][cid]['doctor_id'], 'D-1')

    def test_admin_creates_consultation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/consultations/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'X', 'notes': '',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_patient_cannot_create_consultation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token()}')
        resp = self.client.post('/api/consultations/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'X',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_lists_own_consultations(self):
        self._seed_consultation('C-1', doctor_id='D-1')
        self._seed_consultation('C-2', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.get('/api/consultations/')
        self.assertEqual(resp.status_code, 200)
        ids = [c['consultation_id'] for c in resp.json()]
        self.assertEqual(ids, ['C-1'])

    def test_patient_lists_own_consultations(self):
        self._seed_consultation('C-1', patient_id='P-1')
        self._seed_consultation('C-2', patient_id='P-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/consultations/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_admin_lists_all_consultations(self):
        self._seed_consultation('C-1')
        self._seed_consultation('C-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/consultations/')
        self.assertEqual(len(resp.json()), 2)

    def test_doctor_retrieves_own_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.get('/api/consultations/C-1/')
        self.assertEqual(resp.status_code, 200)

    def test_patient_retrieves_other_consultation_forbidden(self):
        self._seed_consultation('C-1', patient_id='P-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/consultations/C-1/')
        self.assertEqual(resp.status_code, 403)

    def test_consultation_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/consultations/C-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_doctor_updates_own_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/consultations/C-1/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'Updated', 'notes': '',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['consultations']['C-1']['diagnosis'], 'Updated')

    def test_doctor_cannot_update_other_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/consultations/C-1/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'Hacked',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_deletes_own_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/consultations/C-1/')
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('C-1', self.fake.store['consultations'])

    def test_doctor_cannot_delete_other_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/consultations/C-1/')
        self.assertEqual(resp.status_code, 403)

    def test_patient_cannot_delete_consultation(self):
        self._seed_consultation('C-1', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.delete('/api/consultations/C-1/')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_cannot_update_other_doctor_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/consultations/C-1/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'X',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_admin_full_updates_consultation(self):
        self._seed_consultation('C-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.put('/api/consultations/C-1/', {
            'slot_id': 'S-1', 'doctor_id': 'D-1', 'patient_id': 'P-1',
            'consultation_date': '2026-10-01', 'diagnosis': 'Admin Updated',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['consultations']['C-1']['diagnosis'], 'Admin Updated')


# ---------------------------------------------------------------------------
#  Prescription Management
# ---------------------------------------------------------------------------

class PrescriptionManagementTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def _doctor_token(self, doctor_id='D-1'):
        uid = self.seed_user(f'd@{doctor_id}.com', 'pw', 'Dr', 'doctor', doctor_id)
        return self.token_for(uid, 'doctor', doctor_id)

    def _patient_token(self, patient_id='P-1'):
        uid = self.seed_user(f'p@{patient_id}.com', 'pw', 'Pat', 'patient', patient_id)
        return self.token_for(uid, 'patient', patient_id)

    def _seed_consultation(self, cid='C-1', doctor_id='D-1', patient_id='P-1'):
        self.fake.store['consultations'][cid] = {
            'consultation_id': cid, 'slot_id': 'S-1',
            'doctor_id': doctor_id, 'patient_id': patient_id,
            'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }

    def _seed_prescription(self, rxid='Rx-1', doctor_id='D-1', patient_id='P-1', consultation_id='C-1'):
        self.fake.store['prescriptions'][rxid] = {
            'prescription_id': rxid, 'consultation_id': consultation_id,
            'doctor_id': doctor_id, 'patient_id': patient_id,
            'medications': [{'name': 'Aspirin', 'dosage': '100mg', 'frequency': '1x/day',
                             'duration': '7 days', 'notes': ''}],
            'instructions': 'Take with food', 'prescribed_date': '2026-09-20',
        }

    def test_doctor_lists_own_prescriptions(self):
        self._seed_prescription('Rx-1', doctor_id='D-1')
        self._seed_prescription('Rx-2', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.get('/api/prescriptions/')
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]['prescription_id'], 'Rx-1')

    def test_patient_lists_own_prescriptions(self):
        self._seed_prescription('Rx-1', patient_id='P-1')
        self._seed_prescription('Rx-2', patient_id='P-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/prescriptions/')
        self.assertEqual(len(resp.json()), 1)

    def test_admin_lists_all_prescriptions(self):
        self._seed_prescription('Rx-1')
        self._seed_prescription('Rx-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/prescriptions/')
        self.assertEqual(len(resp.json()), 2)

    def test_patient_retrieves_own_prescription(self):
        self._seed_prescription('Rx-1', patient_id='P-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/prescriptions/Rx-1/')
        self.assertEqual(resp.status_code, 200)

    def test_patient_retrieves_other_prescription_forbidden(self):
        self._seed_prescription('Rx-1', patient_id='P-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/prescriptions/Rx-1/')
        self.assertEqual(resp.status_code, 403)

    def test_prescription_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/prescriptions/Rx-NONE/')
        self.assertEqual(resp.status_code, 404)

    def test_doctor_updates_own_prescription(self):
        self._seed_prescription('Rx-1', doctor_id='D-1')
        self._seed_consultation('C-1', doctor_id='D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/prescriptions/Rx-1/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-01', 'instructions': 'Updated',
            'medications': [{'name': 'New Med', 'dosage': '50mg', 'frequency': '2x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_doctor_cannot_update_other_prescription(self):
        self._seed_prescription('Rx-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.put('/api/prescriptions/Rx-1/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-01',
            'medications': [{'name': 'X', 'dosage': '1mg', 'frequency': '1x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_doctor_deletes_own_prescription(self):
        self._seed_prescription('Rx-1', doctor_id='D-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/prescriptions/Rx-1/')
        self.assertEqual(resp.status_code, 204)
        self.assertNotIn('Rx-1', self.fake.store['prescriptions'])

    def test_doctor_cannot_delete_other_prescription(self):
        self._seed_prescription('Rx-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.delete('/api/prescriptions/Rx-1/')
        self.assertEqual(resp.status_code, 403)

    def test_patient_cannot_create_prescription(self):
        self._seed_consultation('C-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token()}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-01',
            'medications': [{'name': 'M', 'dosage': '1mg', 'frequency': '1x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_admin_creates_prescription_any_consultation(self):
        self._seed_consultation('C-1', doctor_id='D-2')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-01',
            'medications': [{'name': 'Drug', 'dosage': '10mg', 'frequency': '1x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_doctor_prescription_auto_fills_patient_id(self):
        self._seed_consultation('C-1', doctor_id='D-1', patient_id='P-99')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'WRONG', 'doctor_id': 'WRONG',
            'prescribed_date': '2026-10-01',
            'medications': [{'name': 'M', 'dosage': '1mg', 'frequency': '1x/day'}],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        rx_id = resp.json()['id']
        self.assertEqual(self.fake.store['prescriptions'][rx_id]['patient_id'], 'P-99')
        self.assertEqual(self.fake.store['prescriptions'][rx_id]['doctor_id'], 'D-1')

    def test_prescription_with_empty_medications_accepted(self):
        self._seed_consultation('C-1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': 'C-1', 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-01', 'medications': [],
        }, format='json')
        self.assertEqual(resp.status_code, 201)


# ---------------------------------------------------------------------------
#  Treatment History (admin sees all, doctor sees own patients only)
# ---------------------------------------------------------------------------

class TreatmentHistoryComprehensiveTests(FirestoreTestCase):

    def _admin_token(self):
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        return self.token_for(uid, 'admin')

    def _doctor_token(self, doctor_id='D-1'):
        uid = self.seed_user(f'd@{doctor_id}.com', 'pw', 'Dr', 'doctor', doctor_id)
        return self.token_for(uid, 'doctor', doctor_id)

    def _patient_token(self, patient_id='P-1'):
        uid = self.seed_user(f'p@{patient_id}.com', 'pw', 'Pat', 'patient', patient_id)
        return self.token_for(uid, 'patient', patient_id)

    def test_admin_sees_all_history(self):
        self.fake.store['consultations']['C-1'] = {
            'consultation_id': 'C-1', 'slot_id': 'S-1', 'doctor_id': 'D-1',
            'patient_id': 'P-1', 'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }
        self.fake.store['consultations']['C-2'] = {
            'consultation_id': 'C-2', 'slot_id': 'S-2', 'doctor_id': 'D-2',
            'patient_id': 'P-2', 'consultation_date': '2026-09-21', 'notes': '', 'diagnosis': 'Cold',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._admin_token()}')
        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_doctor_does_not_see_other_doctors_records(self):
        self.fake.store['consultations']['C-1'] = {
            'consultation_id': 'C-1', 'slot_id': 'S-1', 'doctor_id': 'D-1',
            'patient_id': 'P-1', 'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }
        self.fake.store['consultations']['C-2'] = {
            'consultation_id': 'C-2', 'slot_id': 'S-2', 'doctor_id': 'D-2',
            'patient_id': 'P-1', 'consultation_date': '2026-09-21', 'notes': '', 'diagnosis': 'Cold',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        ids = [item['consultation_id'] for item in resp.json() if item['type'] == 'consultation']
        self.assertEqual(ids, ['C-1'])

    def test_history_mixed_consultations_and_prescriptions(self):
        self.fake.store['consultations']['C-1'] = {
            'consultation_id': 'C-1', 'slot_id': 'S-1', 'doctor_id': 'D-1',
            'patient_id': 'P-1', 'consultation_date': '2026-09-20', 'notes': '', 'diagnosis': 'Flu',
        }
        self.fake.store['prescriptions']['Rx-1'] = {
            'prescription_id': 'Rx-1', 'consultation_id': 'C-1',
            'patient_id': 'P-1', 'doctor_id': 'D-1',
            'medications': [{'name': 'X', 'dosage': '1mg', 'frequency': '1x/day'}],
            'instructions': '', 'prescribed_date': '2026-09-20',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
        types = {item['type'] for item in resp.json()}
        self.assertEqual(types, {'consultation', 'prescription'})

    def test_history_sorted_by_date(self):
        self.fake.store['consultations']['C-1'] = {
            'consultation_id': 'C-1', 'slot_id': 'S-1', 'doctor_id': 'D-1',
            'patient_id': 'P-1', 'consultation_date': '2026-09-25', 'notes': '', 'diagnosis': 'Flu',
        }
        self.fake.store['prescriptions']['Rx-1'] = {
            'prescription_id': 'Rx-1', 'consultation_id': 'C-1',
            'patient_id': 'P-1', 'doctor_id': 'D-1',
            'medications': [{'name': 'X', 'dosage': '1mg', 'frequency': '1x/day'}],
            'instructions': '', 'prescribed_date': '2026-09-10',
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/treatment-history/P-1/')
        dates = [item.get('consultation_date') or item.get('prescribed_date') for item in resp.json()]
        self.assertEqual(dates, ['2026-09-10', '2026-09-25'])


# ---------------------------------------------------------------------------
#  End-to-End Appointment Flow (patient books -> doctor completes -> patient sees history)
# ---------------------------------------------------------------------------

class EndToEndFlowTests(FirestoreTestCase):

    def _doctor_token(self, doctor_id='D-1'):
        uid = self.seed_user(f'd@{doctor_id}.com', 'pw', 'Dr', 'doctor', doctor_id)
        return self.token_for(uid, 'doctor', doctor_id)

    def _patient_token(self, patient_id='P-1'):
        uid = self.seed_user(f'p@{patient_id}.com', 'pw', 'Pat', 'patient', patient_id)
        return self.token_for(uid, 'patient', patient_id)

    def test_full_appointment_lifecycle(self):
        self.seed_doctor('D-1', 'Dr Wilson')
        self.seed_patient('P-1', 'Alice')

        # Step 1: Doctor creates availability
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Monday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
            'appointment_date': '2026-10-06',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        slot_id = resp.json()['id']

        # Step 2: Patient books slot
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch(f'/api/slots/{slot_id}/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots'][slot_id]['patient_id'], 'P-1')
        self.assertEqual(self.fake.store['appointment_slots'][slot_id]['status'], 'Booked')

        # Step 3: Doctor completes consultation
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.patch(f'/api/slots/{slot_id}/', {
            'status': 'Completed',
            'consultation': {'diagnosis': 'Seasonal Flu', 'notes': 'Prescribe Tamiflu'},
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        consultation_id = resp.json()['consultation_id']
        self.assertTrue(consultation_id.startswith('C-'))
        self.assertEqual(self.fake.store['appointment_slots'][slot_id]['status'], 'Completed')

        # Step 4: Doctor creates prescription
        resp = self.client.post('/api/prescriptions/', {
            'consultation_id': consultation_id, 'patient_id': 'P-1', 'doctor_id': 'D-1',
            'prescribed_date': '2026-10-06',
            'medications': [{'name': 'Tamiflu', 'dosage': '75mg', 'frequency': '2x/day',
                             'duration': '5 days', 'notes': 'Take with food'}],
            'instructions': 'Complete full course',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        prescription_id = resp.json()['id']

        # Step 5: Patient sees treatment history
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.get('/api/treatment-history/P-1/')
        self.assertEqual(resp.status_code, 200)
        history = resp.json()
        self.assertEqual(len(history), 2)
        types = {item['type'] for item in history}
        self.assertEqual(types, {'consultation', 'prescription'})

        # Step 6: Patient sees prescription
        resp = self.client.get(f'/api/prescriptions/{prescription_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['medications'][0]['name'], 'Tamiflu')

    def test_patient_cancels_and_rebooks(self):
        self.seed_doctor('D-1')
        self.seed_patient('P-1')

        # Doctor creates slot
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Tuesday',
            'start_time': '10:00:00', 'end_time': '11:00:00',
        }, format='json')
        slot_id = resp.json()['id']

        # Patient books
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        resp = self.client.patch(f'/api/slots/{slot_id}/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 200)

        # Patient cancels
        resp = self.client.patch(f'/api/slots/{slot_id}/', {'status': 'Available'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots'][slot_id]['status'], 'Available')

        # Patient rebooks
        resp = self.client.patch(f'/api/slots/{slot_id}/', {'status': 'Booked'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.fake.store['appointment_slots'][slot_id]['patient_id'], 'P-1')

    def test_doctor_schedule_shows_patient_name_after_booking(self):
        self.seed_doctor('D-1')
        self.seed_patient('P-1', 'Alice Smith')

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Wednesday',
            'start_time': '11:00:00', 'end_time': '12:00:00',
        }, format='json')
        slot_id = resp.json()['id']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._patient_token("P-1")}')
        self.client.patch(f'/api/slots/{slot_id}/', {'status': 'Booked'}, format='json')

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self._doctor_token("D-1")}')
        resp = self.client.get(f'/api/slots/{slot_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.json()['patient_details'])
        self.assertEqual(resp.json()['patient_details']['full_name'], 'Alice Smith')

    def test_admin_can_do_everything(self):
        self.seed_doctor('D-1')
        self.seed_patient('P-1')
        token = secrets.token_hex(16)
        uid = self.seed_user('admin@medehr.com', 'pw', 'Admin', 'admin')
        token = self.token_for(uid, 'admin')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # Create slot
        resp = self.client.post('/api/slots/', {
            'doctor_id': 'D-1', 'day_of_week': 'Thursday',
            'start_time': '09:00:00', 'end_time': '10:00:00',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        # List patients
        resp = self.client.get('/api/patients/')
        self.assertEqual(resp.status_code, 200)

        # List doctors
        resp = self.client.get('/api/doctors/')
        self.assertEqual(resp.status_code, 200)

        # List slots
        resp = self.client.get('/api/slots/')
        self.assertEqual(resp.status_code, 200)