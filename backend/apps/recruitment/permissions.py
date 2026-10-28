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


class IsAgencyAdmin(BasePermission):
    """
    US-29-T3: Allows access only to authenticated users who have the AGENCY_ADMIN role.
    """
    message = "Access forbidden: Only users with the Agency Admin role can manage client companies."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == User.Role.AGENCY_ADMIN
        )


class IsClientAgencyOwner(BasePermission):
    """
    US-29-T3: Object-level permission to ensure only the Agency Admin who owns
    the ClientCompany can view or edit it.
    """
    message = "Access forbidden: You cannot view or modify another agency's client company."

    def has_object_permission(self, request, view, obj):
        agency_owner = getattr(obj, 'agency', None)
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == User.Role.AGENCY_ADMIN and
            agency_owner == request.user
        )


class IsHRManagerOrAgencyAdmin(BasePermission):
    """
    US-30: Allows access only to authenticated users who have either
    the HR_MANAGER or the AGENCY_ADMIN role.
    """
    message = "Access forbidden: Only HR Managers or Agency Administrators can access this recruitment resource."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in [User.Role.HR_MANAGER, User.Role.AGENCY_ADMIN]
        )


class IsAgencyRoomOwner(BasePermission):
    """
    US-30-T5: Object-level permission to ensure only the Agency Admin who owns
    the client room can view or modify it.
    """
    message = "Access forbidden: You cannot view or modify another agency's room."

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == User.Role.AGENCY_ADMIN and
            (
                obj.created_by == request.user or
                (getattr(obj, 'client_company', None) and obj.client_company.agency == request.user)
            )
        )


class IsRoomOwnerOrAdmin(BasePermission):
    """
    US-33-T5: Ensures only the creator/owner of the RecruitmentRoom (HR Manager)
    or the Agency Admin managing the client company can access and download reports.
    """
    message = "Access forbidden: Only authorized HR Managers or Agency Administrators can access this report."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in [User.Role.HR_MANAGER, User.Role.AGENCY_ADMIN]
        )

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Support both CandidateApplication and RecruitmentRoom objects
        room = getattr(obj, 'room', None) or obj
        created_by = getattr(room, 'created_by', None)
        client_company = getattr(room, 'client_company', None)

        # Room creator check
        if created_by == request.user:
            return True

        # Agency Admin managing client company check
        if client_company and getattr(client_company, 'agency', None) == request.user:
            return True

        return False


