from rest_framework import serializers


class PatientRecordSerializer(serializers.Serializer):
    patient_id = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=100)
    contact_number = serializers.CharField(max_length=15)
    email_address = serializers.EmailField()
    date_of_birth = serializers.DateField()
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    blood_group = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    address = serializers.CharField(max_length=250, required=False, allow_blank=True, default='')
    emergency_contact_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    emergency_contact_number = serializers.CharField(max_length=15, required=False, allow_blank=True, default='')


class DoctorProfileSerializer(serializers.Serializer):
    doctor_id = serializers.CharField(max_length=20)
    doctor_name = serializers.CharField(max_length=100)
    specialization = serializers.CharField(max_length=100)
    email_address = serializers.EmailField(required=False, allow_blank=True, allow_null=True, default='')


class AppointmentSlotSerializer(serializers.Serializer):
    slot_id = serializers.CharField(read_only=True)
    doctor_id = serializers.CharField(max_length=20)
    patient_id = serializers.CharField(max_length=20, allow_blank=True, allow_null=True, default=None)
    appointment_date = serializers.DateField(allow_null=True, required=False)
    day_of_week = serializers.CharField(max_length=20)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    status = serializers.ChoiceField(choices=['Available', 'Booked', 'Completed'], default='Available')
    doctor_details = serializers.DictField(read_only=True, required=False)
    patient_details = serializers.DictField(read_only=True, required=False)


class MedicationItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    dosage = serializers.CharField(max_length=50)
    frequency = serializers.CharField(max_length=50)
    duration = serializers.CharField(max_length=50, allow_blank=True, required=False, default='')
    notes = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')


class ConsultationSerializer(serializers.Serializer):
    consultation_id = serializers.CharField(read_only=True)
    slot_id = serializers.CharField(max_length=30)
    doctor_id = serializers.CharField(max_length=20)
    patient_id = serializers.CharField(max_length=20)
    consultation_date = serializers.DateField()
    notes = serializers.CharField(max_length=2000, allow_blank=True, required=False, default='')
    diagnosis = serializers.CharField(max_length=500)
    doctor_details = serializers.DictField(read_only=True, required=False)
    patient_details = serializers.DictField(read_only=True, required=False)


class PrescriptionSerializer(serializers.Serializer):
    prescription_id = serializers.CharField(read_only=True)
    consultation_id = serializers.CharField(max_length=30)
    patient_id = serializers.CharField(max_length=20)
    doctor_id = serializers.CharField(max_length=20)
    medications = MedicationItemSerializer(many=True)
    instructions = serializers.CharField(max_length=1000, allow_blank=True, required=False, default='')
    prescribed_date = serializers.DateField()
    consultation_details = serializers.DictField(read_only=True, required=False)
