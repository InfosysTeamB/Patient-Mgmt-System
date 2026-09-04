from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientRecordViewSet, DoctorProfileViewSet, AppointmentSlotViewSet, login_view, register_view

router = DefaultRouter()
router.register(r'patients', PatientRecordViewSet, basename='patient')
router.register(r'doctors', DoctorProfileViewSet, basename='doctor')
router.register(r'slots', AppointmentSlotViewSet, basename='slot')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
]