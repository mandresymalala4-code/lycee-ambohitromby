from rest_framework.permissions import SAFE_METHODS, BasePermission


class EstAdmin(BasePermission):
    message = 'Accès réservé à l\'administrateur.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class AdminOuLecture(BasePermission):
    """Administrateur : tout ; professeur : lecture seule."""
    message = 'Accès réservé à l\'administrateur.'

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        return u.role == 'ADMIN' or request.method in SAFE_METHODS
