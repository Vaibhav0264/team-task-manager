from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_admin


class IsProjectMemberOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'members'):
            return obj.members.filter(pk=request.user.pk).exists()
        if hasattr(obj, 'project'):
            return obj.project.members.filter(pk=request.user.pk).exists()
        return False


class CanEditTask(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if request.method in SAFE_METHODS:
            return obj.project.members.filter(pk=request.user.pk).exists()
        # Members can only update status of their assigned tasks
        return (obj.assigned_to == request.user and
                obj.project.members.filter(pk=request.user.pk).exists())
