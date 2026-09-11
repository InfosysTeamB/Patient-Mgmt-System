from rest_framework import serializers


class PatientRecordSerializer(serializers.Serializer):
    patient_id = serializers.CharField(max_length=20)
    full_name = serializers.CharField(max_length=100)
    contact_number = serializers.CharField(max_length=15)
    email_address = serializers.EmailField()
    date_of_birth = serializers.DateField()


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
    status = serializers.ChoiceField(choices=['Available', 'Booked'], default='Available')
    doctor_details = serializers.DictField(read_only=True, required=False)
    patient_details = serializers.DictField(read_only=True, required=False)
