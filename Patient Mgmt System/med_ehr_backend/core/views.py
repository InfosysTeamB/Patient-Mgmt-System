import datetime
import secrets
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1 import DELETE_FIELD
from firebase_config import db
from .auth import TOKENS_COL
from .permissions import IsAdmin, IsDoctor, IsDoctorOrAdmin, IsPatient, IsStaffOrAdmin
from .serializers import PatientRecordSerializer, DoctorProfileSerializer, AppointmentSlotSerializer, ConsultationSerializer, PrescriptionSerializer


PATIENTS_COL = 'patients'
DOCTORS_COL = 'doctors'
SLOTS_COL = 'appointment_slots'
USERS_COL = 'users'
CONSULTATIONS_COL = 'consultations'
PRESCRIPTIONS_COL = 'prescriptions'


DEFAULT_PROFILE_PASSWORD = 'medehr@123'


def _generate_token():
    return secrets.token_hex(16)


def _store_token(user_id, role, entity_id):
    """Create/overwrite the token document for a user."""
    token = _generate_token()
    db.collection(TOKENS_COL).document(token).set({
        "user_id": user_id,
        "role": role,
        "entity_id": entity_id,
    })
    return token


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
        role = request.user.role
        patients = []
        for doc in docs:
            data = {"id": doc.id, **doc.to_dict()}
            if role == 'patient' and data.get('patient_id') != request.user.entity_id:
                continue
            patients.append(data)
        return Response(patients)

    def create(self, request):
        if request.user.role != 'admin':
            return Response({"error": "Only admins can create patients"}, status=status.HTTP_403_FORBIDDEN)

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
        if request.user.role == 'patient' and pk != request.user.entity_id:
            return Response({"error": "Not your record"}, status=status.HTTP_403_FORBIDDEN)
        return Response({"id": doc.id, **doc.to_dict()})

    def update(self, request, pk=None):
        self._check_write_access(request, pk)
        serializer = PatientRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        doc_ref = db.collection(PATIENTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.set(_to_firestore_dict(data))
        return Response(data)

    def partial_update(self, request, pk=None):
        self._check_write_access(request, pk)
        doc_ref = db.collection(PATIENTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.update(_to_firestore_dict(request.data))
        return Response({**request.data, "patient_id": pk})

    def _check_write_access(self, request, pk):
        role = request.user.role
        if role == 'admin':
            return
        if role == 'patient' and pk == request.user.entity_id:
            return
        raise PermissionDenied("You do not have permission to modify this record")

    def destroy(self, request, pk=None):
        if request.user.role != 'admin':
            return Response({"error": "Only admins can delete patients"}, status=status.HTTP_403_FORBIDDEN)
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
        if request.user.role != 'admin':
            return Response({"error": "Only admins can create doctors"}, status=status.HTTP_403_FORBIDDEN)

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
        self._check_write_access(request, pk)
        serializer = DoctorProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.set(_to_firestore_dict(data))
        return Response(data)

    def partial_update(self, request, pk=None):
        self._check_write_access(request, pk)
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.update(_to_firestore_dict(request.data))
        return Response({**request.data, "doctor_id": pk})

    def _check_write_access(self, request, pk):
        role = request.user.role
        if role == 'admin':
            return
        if role == 'doctor' and pk == request.user.entity_id:
            return
        raise PermissionDenied("You do not have permission to modify this record")

    def destroy(self, request, pk=None):
        if request.user.role != 'admin':
            return Response({"error": "Only admins can delete doctors"}, status=status.HTTP_403_FORBIDDEN)
        doc_ref = db.collection(DOCTORS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppointmentSlotViewSet(viewsets.ViewSet):
    permission_classes = [IsStaffOrAdmin]

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
        role = request.user.role
        if role not in ('admin', 'doctor'):
            return Response({"error": "Only admins and doctors can create slots"}, status=status.HTTP_403_FORBIDDEN)

        serializer = AppointmentSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("doctor_details", None)
        data.pop("patient_details", None)
        data.pop("slot_id", None)

        if role == 'doctor':
            data['doctor_id'] = request.user.entity_id

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

        if request.user.role == 'doctor' and data.get('doctor_id') != request.user.entity_id:
            return Response({"error": "You can only edit your own slots"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref.set(_to_firestore_dict(data))
        return Response({"id": pk, **data})

    def partial_update(self, request, pk=None):
        doc_ref = db.collection(SLOTS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)

        current_data = current.to_dict() or {}
        incoming_status = request.data.get('status', current_data.get('status'))
        role = request.user.role

        # Doctors can only modify their own slots
        if role == 'doctor' and current_data.get('doctor_id') != request.user.entity_id:
            return Response({"error": "You can only modify your own slots"}, status=status.HTTP_403_FORBIDDEN)

        # Prevent a second patient from booking a slot that is already booked
        if incoming_status == 'Booked':
            if role == 'doctor':
                return Response({"error": "Doctors cannot book slots"}, status=status.HTTP_403_FORBIDDEN)
            if current_data.get('status') == 'Booked':
                return Response({"error": "Slot is already booked"}, status=status.HTTP_400_BAD_REQUEST)
            if current_data.get('status') not in ('Available', 'Completed'):
                return Response({"error": "Slot cannot be booked"}, status=status.HTTP_400_BAD_REQUEST)
            if role == 'patient':
                request.user._booking_overrides = {
                    'patient_id': request.user.entity_id,
                    'doctor_id': current_data.get('doctor_id'),
                }

        # Patient canceling their own booking: Booked -> Available
        if role == 'patient' and incoming_status == 'Available':
            if current_data.get('patient_id') != request.user.entity_id:
                return Response({"error": "You can only cancel your own bookings"}, status=status.HTTP_403_FORBIDDEN)
            if current_data.get('status') != 'Booked':
                return Response({"error": "Slot is not booked"}, status=status.HTTP_400_BAD_REQUEST)

        # Completing a consultation: Booked -> Completed
        if incoming_status == 'Completed':
            if role not in ('doctor', 'admin'):
                return Response({"error": "Only doctors can complete consultations"}, status=status.HTTP_403_FORBIDDEN)
            if current_data.get('status') != 'Booked':
                return Response({"error": "Only booked slots can be completed"}, status=status.HTTP_400_BAD_REQUEST)

            consultation = request.data.get('consultation', {})
            if not isinstance(consultation, dict):
                consultation = {}
            diagnosis = (consultation).get('diagnosis', '')
            notes = (consultation).get('notes', '')
            if not diagnosis:
                return Response({"error": "A diagnosis is required to complete a consultation"}, status=status.HTTP_400_BAD_REQUEST)

            consultation_id = self._create_consultation(current_data, diagnosis, notes)
            self._complete_slot(doc_ref, current_data, consultation_id)
            return Response({"id": pk, "status": "Completed", "consultation_id": consultation_id})

        booking_overrides = getattr(request.user, '_booking_overrides', None)
        update_data = {k: v for k, v in request.data.items() if k != 'consultation'}
        if booking_overrides:
            update_data.update(booking_overrides)
        update_data = _to_firestore_dict(update_data)
        # A null/blank patient_id means the patient canceled and the field
        # must actually be removed (None values are normally dropped).
        if 'patient_id' in request.data and request.data.get('patient_id') in (None, ''):
            update_data['patient_id'] = DELETE_FIELD

        doc_ref.update(update_data)
        response_data = {k: v for k, v in request.data.items() if k != 'consultation'}
        if booking_overrides:
            response_data.update(booking_overrides)
        return Response({**response_data, "id": pk})

    def _create_consultation(self, slot_data, diagnosis, notes):
        consultation_id = 'C-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        consultation_date = slot_data.get('appointment_date') or datetime.date.today().isoformat()
        db.collection(CONSULTATIONS_COL).document(consultation_id).set({
            "consultation_id": consultation_id,
            "slot_id": slot_data.get('slot_id', ''),
            "doctor_id": slot_data.get('doctor_id', ''),
            "patient_id": slot_data.get('patient_id', ''),
            "consultation_date": consultation_date,
            "notes": notes,
            "diagnosis": diagnosis,
        })
        return consultation_id

    def _complete_slot(self, doc_ref, slot_data, consultation_id):
        doc_ref.update({
            "status": "Completed",
            "consultation_id": consultation_id,
        })

    def destroy(self, request, pk=None):
        doc_ref = db.collection(SLOTS_COL).document(pk)
        if not doc_ref.get().exists:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'doctor':
            current = doc_ref.get().to_dict() or {}
            if current.get('doctor_id') != request.user.entity_id:
                return Response({"error": "You can only delete your own slots"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _filter_own(role, entity_id, owner_field, docs):
    """Yield docs a user is allowed to read, based on role."""
    for doc in docs:
        data = doc.to_dict() or {}
        if role == 'admin':
            yield doc, data
        elif role == 'doctor' and data.get('doctor_id') == entity_id:
            yield doc, data
        elif role == 'patient' and data.get('patient_id') == entity_id:
            yield doc, data


class ConsultationViewSet(viewsets.ViewSet):
    permission_classes = [IsStaffOrAdmin]

    def _get_details(self, data):
        doctor_details = None
        patient_details = None
        if data.get('doctor_id'):
            doc = db.collection(DOCTORS_COL).document(data['doctor_id']).get()
            if doc.exists:
                doctor_details = doc.to_dict()
        if data.get('patient_id'):
            doc = db.collection(PATIENTS_COL).document(data['patient_id']).get()
            if doc.exists:
                patient_details = doc.to_dict()
        return doctor_details, patient_details

    def list(self, request):
        docs = db.collection(CONSULTATIONS_COL).stream()
        consultations = []
        for doc, data in _filter_own(request.user.role, request.user.entity_id, 'doctor_id', docs):
            doctor_details, patient_details = self._get_details(data)
            consultations.append({
                "id": doc.id,
                **data,
                "doctor_details": doctor_details,
                "patient_details": patient_details,
            })
        return Response(consultations)

    def retrieve(self, request, pk=None):
        doc = db.collection(CONSULTATIONS_COL).document(pk).get()
        if not doc.exists:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)
        data = doc.to_dict() or {}

        role = request.user.role
        if role == 'doctor' and data.get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your consultation"}, status=status.HTTP_403_FORBIDDEN)
        if role == 'patient' and data.get('patient_id') != request.user.entity_id:
            return Response({"error": "Not your consultation"}, status=status.HTTP_403_FORBIDDEN)

        doctor_details, patient_details = self._get_details(data)
        return Response({"id": doc.id, **data, "doctor_details": doctor_details, "patient_details": patient_details})

    def create(self, request):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can create consultations"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ConsultationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("doctor_details", None)
        data.pop("patient_details", None)
        data.pop("consultation_id", None)

        if request.user.role == 'doctor':
            data['doctor_id'] = request.user.entity_id

        consultation_id = 'C-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        db.collection(CONSULTATIONS_COL).document(consultation_id).set(_to_firestore_dict({
            **data,
            "consultation_id": consultation_id,
        }))
        return Response({"id": consultation_id, **data}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can update consultations"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref = db.collection(CONSULTATIONS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'doctor' and (current.to_dict() or {}).get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your consultation"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ConsultationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("doctor_details", None)
        data.pop("patient_details", None)
        data.pop("consultation_id", None)
        doc_ref.update(_to_firestore_dict(data))
        return Response({"id": pk, **data})

    def destroy(self, request, pk=None):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can delete consultations"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref = db.collection(CONSULTATIONS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'doctor' and (current.to_dict() or {}).get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your consultation"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PrescriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsStaffOrAdmin]

    def _get_details(self, data):
        consultation_details = None
        if data.get('consultation_id'):
            doc = db.collection(CONSULTATIONS_COL).document(data['consultation_id']).get()
            if doc.exists:
                consultation_details = doc.to_dict()
        return consultation_details

    def list(self, request):
        docs = db.collection(PRESCRIPTIONS_COL).stream()
        prescriptions = []
        for doc, data in _filter_own(request.user.role, request.user.entity_id, 'doctor_id', docs):
            consultation_details = self._get_details(data)
            prescriptions.append({
                "id": doc.id,
                **data,
                "consultation_details": consultation_details,
            })
        return Response(prescriptions)

    def retrieve(self, request, pk=None):
        doc = db.collection(PRESCRIPTIONS_COL).document(pk).get()
        if not doc.exists:
            return Response({"error": "Prescription not found"}, status=status.HTTP_404_NOT_FOUND)
        data = doc.to_dict() or {}

        role = request.user.role
        if role == 'doctor' and data.get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your prescription"}, status=status.HTTP_403_FORBIDDEN)
        if role == 'patient' and data.get('patient_id') != request.user.entity_id:
            return Response({"error": "Not your prescription"}, status=status.HTTP_403_FORBIDDEN)

        consultation_details = self._get_details(data)
        return Response({"id": doc.id, **data, "consultation_details": consultation_details})

    def create(self, request):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can create prescriptions"}, status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Prescription must reference a real consultation
        consultation_doc = db.collection(CONSULTATIONS_COL).document(data['consultation_id']).get()
        if not consultation_doc.exists:
            return Response({"error": "Consultation not found"}, status=status.HTTP_400_BAD_REQUEST)
        consultation = consultation_doc.to_dict() or {}

        if request.user.role == 'doctor':
            if consultation.get('doctor_id') != request.user.entity_id:
                return Response({"error": "Prescription must be linked to your own consultation"}, status=status.HTTP_403_FORBIDDEN)
            data['doctor_id'] = request.user.entity_id
            data['patient_id'] = consultation.get('patient_id', '')

        data.pop("consultation_details", None)
        data.pop("prescription_id", None)

        prescription_id = 'Rx-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        db.collection(PRESCRIPTIONS_COL).document(prescription_id).set(_to_firestore_dict({
            **data,
            "prescription_id": prescription_id,
        }))
        return Response({"id": prescription_id, **data}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can update prescriptions"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref = db.collection(PRESCRIPTIONS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Prescription not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'doctor' and (current.to_dict() or {}).get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your prescription"}, status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("consultation_details", None)
        data.pop("prescription_id", None)
        doc_ref.update(_to_firestore_dict(data))
        return Response({"id": pk, **data})

    def destroy(self, request, pk=None):
        if request.user.role not in ('doctor', 'admin'):
            return Response({"error": "Only doctors can delete prescriptions"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref = db.collection(PRESCRIPTIONS_COL).document(pk)
        current = doc_ref.get()
        if not current.exists:
            return Response({"error": "Prescription not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'doctor' and (current.to_dict() or {}).get('doctor_id') != request.user.entity_id:
            return Response({"error": "Not your prescription"}, status=status.HTTP_403_FORBIDDEN)

        doc_ref.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def treatment_history_view(request, patient_id):
    role = request.user.role
    if role == 'patient' and request.user.entity_id != patient_id:
        return Response({"error": "Not your records"}, status=status.HTTP_403_FORBIDDEN)

    consultations = []
    docs = db.collection(CONSULTATIONS_COL).where(filter=FieldFilter('patient_id', '==', patient_id)).stream()
    for doc in docs:
        data = doc.to_dict() or {}
        if role == 'doctor' and data.get('doctor_id') != request.user.entity_id:
            continue
        consultations.append({"type": "consultation", "id": doc.id, **data})

    prescriptions = []
    docs = db.collection(PRESCRIPTIONS_COL).where(filter=FieldFilter('patient_id', '==', patient_id)).stream()
    for doc in docs:
        data = doc.to_dict() or {}
        if role == 'doctor' and data.get('doctor_id') != request.user.entity_id:
            continue
        prescriptions.append({"type": "prescription", "id": doc.id, **data})

    merged = consultations + prescriptions
    merged.sort(key=lambda item: item.get('consultation_date') or item.get('prescribed_date') or '')
    return Response(merged)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    docs = db.collection(USERS_COL).where(filter=FieldFilter('email', '==', email)).stream()
    for doc in docs:
        user = doc.to_dict()
        if user.get('password') == password:
            token = _store_token(doc.id, user['role'], user.get('entity_id', ''))
            return Response({
                "token": token,
                "id": doc.id,
                "email": user['email'],
                "name": user.get('name', ''),
                "role": user['role'],
                "entity_id": user.get('entity_id', ''),
            })

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
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

    token = _store_token(doc_ref[1].id, role, entity_id)

    return Response({
        "token": token,
        "id": doc_ref[1].id,
        "email": email,
        "name": name,
        "role": role,
        "entity_id": entity_id,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def logout_view(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return Response({"error": "Missing token"}, status=status.HTTP_400_BAD_REQUEST)

    token = auth_header.split(' ', 1)[1].strip()
    token_doc = db.collection(TOKENS_COL).document(token).get()
    if token_doc.exists:
        db.collection(TOKENS_COL).document(token).delete()

    return Response({"message": "Logged out"})
