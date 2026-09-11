from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (PatientRecordViewSet, DoctorProfileViewSet, AppointmentSlotViewSet,
                    ConsultationViewSet, PrescriptionViewSet, login_view, register_view,
                    logout_view, treatment_history_view)

router = DefaultRouter()
router.register(r'patients', PatientRecordViewSet, basename='patient')
router.register(r'doctors', DoctorProfileViewSet, basename='doctor')
router.register(r'slots', AppointmentSlotViewSet, basename='slot')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    path('auth/logout/', logout_view, name='logout'),
    path('treatment-history/<str:patient_id>/', treatment_history_view, name='treatment-history'),
]