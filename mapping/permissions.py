from rest_framework.permissions import BasePermission


class IsReviewerOrAdmin(BasePermission):
    message = 'Apenas revisores ou administradores podem acessar este recurso.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.groups.filter(name='Revisor').exists()
