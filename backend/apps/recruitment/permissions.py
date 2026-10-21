from rest_framework.permissions import BasePermission
from apps.authentication.models import User


class IsHRManager(BasePermission):
    """
    Allows access only to authenticated users who have the HR_MANAGER role.
    """
    message = "Access forbidden: Only users with the HR Manager role can manage recruitment rooms."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.HR_MANAGER
        )


class IsRoomOwner(BasePermission):
    """
    Object-level permission to only allow creators/owners of a room to view or edit it.
    """
    message = "Access forbidden: You cannot view or modify another HR manager's room."

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            obj.created_by == request.user
        )


class IsApplicationRoomOwner(BasePermission):
    """
    US-26-T5: Object-level permission to ensure only the HR Manager who owns
    the RecruitmentRoom can view applicant details and record human decisions.
    """
    message = "Access forbidden: Only the HR Manager who owns this recruitment room can review or record decisions."

    def has_object_permission(self, request, view, obj):
        room = getattr(obj, 'room', None)
        room_owner = getattr(room, 'created_by', None) if room else None
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.HR_MANAGER and
            room_owner == request.user
        )

