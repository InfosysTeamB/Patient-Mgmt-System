from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'admin'


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'doctor'


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'patient'


class IsDoctorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) in ('doctor', 'admin')


class IsStaffOrAdmin(BasePermission):
    """Admin, or a doctor/patient acting on their own records (used with
    object-level checks in the views)."""
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) in ('admin', 'doctor', 'patient')


def get_role(request):
    return getattr(request.user, 'role', '')