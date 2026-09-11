import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1 import DELETE_FIELD
from firebase_config import db
from .serializers import PatientRecordSerializer, DoctorProfileSerializer, AppointmentSlotSerializer


PATIENTS_COL = 'patients'
DOCTORS_COL = 'doctors'
SLOTS_COL = 'appointment_slots'
USERS_COL = 'users'


DEFAULT_PROFILE_PASSWORD = 'medehr@123'


def _create_user_for_profile(email, name, role, entity_id):
    """Create a login account for a patient/doctor registered by the admin.

    Returns True if a new account was created, False if the email is missing
    or already registered.
    """
    email = (email or '').strip()
    if not email:
        return False

    existing = db.collection(USERS_COL).where(filter=FieldFilter('email', '==', email)).stream()
    for _ in existing:
        return False

    db.collection(USERS_COL).add({
        "email": email,
        "password": DEFAULT_PROFILE_PASSWORD,
        "name": name,
        "role": role,
        "entity_id": entity_id,
    })
    return True


def _to_firestore_dict(data):
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime.date):
            result[key] = value.isoformat()
        elif isinstance(value, datetime.time):
            result[key] = value.isoformat()
        elif value is not None:
            result[key] = value
    return result


class PatientRecordViewSet(viewsets.ViewSet):

    def list(self, request):
        docs = db.collection(PATIENTS_COL).stream()
        patients = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        return Response(patients)

    def create(self, request):
        serializer = PatientRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        patient_id = data['patient_id']

        if db.collection(PATIENTS_COL).document(patient_id).get().exists:
            return Response({"error": "Patient ID already exists"}, status=status.HTTP_400_BAD_REQUEST)

        db.collection(PATIENTS_COL).document(patient_id).set(_to_firestore_dict(data))
        login_created = _create_user_for_profile(
            data.get('email_address'), data.get('full_name'), 'patient', patient_id
        )
        return Response({**data, "login_created": login_created}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        doc = db.collection(PATIENTS_COL).document(pk).get()
        if not doc.exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": doc.id, **doc.to_dict()})

    def update(self, request, pk=None):
        serializer = PatientRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_ref = db.collection(PATIENTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.set(_to_firestore_dict(serializer.validated_data))
        return Response(serializer.validated_data)

    def partial_update(self, request, pk=None):
        doc_ref = db.collection(PATIENTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.update(_to_firestore_dict(request.data))
        return Response({**request.data, "patient_id": pk})

    def destroy(self, request, pk=None):
        doc_ref = db.collection(PATIENTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DoctorProfileViewSet(viewsets.ViewSet):

    def list(self, request):
        docs = db.collection(DOCTORS_COL).stream()
        doctors = [{"id": doc.id, **doc.to_dict()} for doc in docs]
        return Response(doctors)

    def create(self, request):
        serializer = DoctorProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        doctor_id = data['doctor_id']

        if db.collection(DOCTORS_COL).document(doctor_id).get().exists:
            return Response({"error": "Doctor ID already exists"}, status=status.HTTP_400_BAD_REQUEST)

        db.collection(DOCTORS_COL).document(doctor_id).set(_to_firestore_dict(data))
        login_created = _create_user_for_profile(
            data.get('email_address'), data.get('doctor_name'), 'doctor', doctor_id
        )
        return Response({**data, "login_created": login_created}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        doc = db.collection(DOCTORS_COL).document(pk).get()
        if not doc.exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"id": doc.id, **doc.to_dict()})

    def update(self, request, pk=None):
        serializer = DoctorProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.set(_to_firestore_dict(serializer.validated_data))
        return Response(serializer.validated_data)

    def partial_update(self, request, pk=None):
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.update(_to_firestore_dict(request.data))
        return Response({**request.data, "doctor_id": pk})

    def destroy(self, request, pk=None):
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppointmentSlotViewSet(viewsets.ViewSet):

    def _get_details(self, slot_data):
        doctor_details = None
        patient_details = None

        if slot_data.get("doctor_id"):
            doc = db.collection(DOCTORS_COL).document(slot_data["doctor_id"]).get()
            if doc.exists:
                doctor_details = doc.to_dict()

        if slot_data.get("patient_id"):
            doc = db.collection(PATIENTS_COL).document(slot_data["patient_id"]).get()
            if doc.exists:
                patient_details = doc.to_dict()

        return doctor_details, patient_details

    def list(self, request):
        docs = db.collection(SLOTS_COL).stream()
        slots = []
        for doc in docs:
            data = doc.to_dict()
            doctor_details, patient_details = self._get_details(data)
            slots.append({
                "id": doc.id,
                **data,
                "doctor_details": doctor_details,
                "patient_details": patient_details,
            })
        return Response(slots)

    def create(self, request):
        serializer = AppointmentSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("doctor_details", None)
        data.pop("patient_details", None)
        data.pop("slot_id", None)

        doc_ref = db.collection(SLOTS_COL).add(_to_firestore_dict(data))
        return Response({"id": doc_ref[1].id, **data}, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        doc = db.collection(SLOTS_COL).document(pk).get()
        if not doc.exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        data = doc.to_dict()
        doctor_details, patient_details = self._get_details(data)
        return Response({
            "id": doc.id,
            **data,
            "doctor_details": doctor_details,
            "patient_details": patient_details,
        })

    def update(self, request, pk=None):
        serializer = AppointmentSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("doctor_details", None)
        data.pop("patient_details", None)
        data.pop("slot_id", None)

        doc_ref = db.collection(SLOTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.set(_to_firestore_dict(data))
        return Response({"id": pk, **data})

    def partial_update(self, request, pk=None):
        doc_ref = db.collection(SLOTS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)

        current_data = current.to_dict() or {}
        incoming_status = request.data.get('status', current_data.get('status'))

        # Prevent a second patient from booking a slot that is already booked
        if incoming_status == 'Booked' and current_data.get('status') == 'Booked':
            return Response({"error": "Slot is already booked"}, status=status.HTTP_400_BAD_REQUEST)

        update_data = _to_firestore_dict(request.data)
        # A null/blank patient_id means the patient canceled and the field
        # must actually be removed (None values are normally dropped).
        if 'patient_id' in request.data and request.data.get('patient_id') in (None, ''):
            update_data['patient_id'] = DELETE_FIELD

        doc_ref.update(update_data)
        return Response({**request.data, "id": pk})

    def destroy(self, request, pk=None):
        doc_ref = db.collection(SLOTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def login_view(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    docs = db.collection(USERS_COL).where(filter=FieldFilter('email', '==', email)).stream()
    for doc in docs:
        user = doc.to_dict()
        if user.get('password') == password:
            return Response({
                "id": doc.id,
                "email": user['email'],
                "name": user.get('name', ''),
                "role": user['role'],
                "entity_id": user.get('entity_id', ''),
            })

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def register_view(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()
    name = request.data.get('name', '').strip()
    role = request.data.get('role', '').strip()
    entity_id = request.data.get('entity_id', '').strip()

    if not email or not password or not role:
        return Response({"error": "Email, password, and role are required"}, status=status.HTTP_400_BAD_REQUEST)

    if role not in ('admin', 'patient', 'doctor'):
        return Response({"error": "Role must be admin, patient, or doctor"}, status=status.HTTP_400_BAD_REQUEST)

    if role == 'admin':
        return Response({"error": "Admin accounts cannot be self-registered"}, status=status.HTTP_400_BAD_REQUEST)

    existing = db.collection(USERS_COL).where(filter=FieldFilter('email', '==', email)).stream()
    for _ in existing:
        return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

    # Self-registration always gets a fresh, unique ID that never collides with
    # an existing patient/doctor record. Any manually-entered entity_id from the
    # registration form is ignored, so a new account can never show an old
    # profile. (Admin is a system role and needs no profile record.)
    if role == 'patient':
        entity_id = 'P-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        db.collection(PATIENTS_COL).document(entity_id).set(_to_firestore_dict({
            "patient_id": entity_id,
            "full_name": name,
            "contact_number": "",
            "email_address": email,
            "date_of_birth": "2000-01-01",
        }))

    elif role == 'doctor':
        entity_id = 'D-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        db.collection(DOCTORS_COL).document(entity_id).set(_to_firestore_dict({
            "doctor_id": entity_id,
            "doctor_name": name,
            "specialization": "General",
        }))

    doc_ref = db.collection(USERS_COL).add({
        "email": email,
        "password": password,
        "name": name,
        "role": role,
        "entity_id": entity_id,
    })

    return Response({
        "id": doc_ref[1].id,
        "email": email,
        "name": name,
        "role": role,
        "entity_id": entity_id,
    }, status=status.HTTP_201_CREATED)
