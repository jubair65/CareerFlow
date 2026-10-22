from rest_framework import permissions


class IsVideoOwner(permissions.BasePermission):
    """
    US-16-T5: Object-level permission to only allow students to access their own presentation videos and analyses.
    Ensures students cannot view, modify, or delete another student's analysis results (tenant isolation).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Object may be PresentationVideo directly
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Object may be a related model with a .video foreign key / one-to-one
        if hasattr(obj, 'video'):
            return obj.video.user == request.user

        return False
