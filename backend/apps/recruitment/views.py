from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RecruitmentRoom
from .serializers import (
    RecruitmentRoomSerializer,
    RoomRequirementsSerializer,
    RoomWeightingSerializer,
    RoomShareLinkSerializer,
    PublicRoomDetailsSerializer,
)
from .permissions import IsHRManager, IsRoomOwner
from .services.matcher_bridge import sync_room_to_job_requirement
from .tokens import (
    generate_secure_share_token,
    validate_share_token,
    build_share_url,
    is_token_expired,
)


class RecruitmentRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD API for HR Recruitment Rooms (US-18, US-19, US-20).
    Strictly isolated so HR Managers can only view and manage their own rooms.
    """
    serializer_class = RecruitmentRoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager, IsRoomOwner]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or user.role != 'HR_MANAGER':
            return RecruitmentRoom.objects.none()
        return RecruitmentRoom.objects.filter(created_by=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Recruitment room created successfully.",
                "room": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {
                "message": "Recruitment room updated successfully.",
                "room": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='requirements')
    def requirements(self, request, pk=None):
        """
        US-19-T2: Manage job role details, experience level, requirements text,
        and required skill tags for a Room.
        """
        room = self.get_object()

        if request.method == 'GET':
            serializer = RoomRequirementsSerializer(room)
            return Response(
                {
                    "room_id": room.id,
                    "title": room.title,
                    "company_name": room.company_name,
                    "requirements": serializer.data,
                    "skill_names": room.get_skill_names(),
                },
                status=status.HTTP_200_OK
            )

        partial = (request.method == 'PATCH')
        serializer = RoomRequirementsSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_room = serializer.save()

        # US-19-T5: Synchronize with CV semantic matching module
        try:
            sync_room_to_job_requirement(updated_room)
        except Exception as e:
            # Non-blocking sync log
            pass

        full_serializer = RecruitmentRoomSerializer(updated_room, context={'request': request})
        return Response(
            {
                "message": "Job role and requirements updated successfully.",
                "room": full_serializer.data,
                "requirements": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='weighting')
    def weighting(self, request, pk=None):
        """
        US-20-T2: Configure evaluation weighting (CV weight % vs Video weight %) for a Room.
        Ensures weights are integers within 0-100 and total exactly 100%.
        """
        room = self.get_object()

        if request.method == 'GET':
            serializer = RoomWeightingSerializer(room)
            return Response(
                {
                    "room_id": room.id,
                    "title": room.title,
                    "company_name": room.company_name,
                    "cv_weight": room.cv_weight,
                    "video_weight": room.video_weight,
                    "weighting": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        partial = (request.method == 'PATCH')
        serializer = RoomWeightingSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_room = serializer.save()

        full_serializer = RecruitmentRoomSerializer(updated_room, context={'request': request})
        return Response(
            {
                "message": "Evaluation weighting updated successfully.",
                "room": full_serializer.data,
                "weighting": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'post'], url_path='link')
    def link(self, request, pk=None):
        """
        US-21-T2: Retrieve or generate shareable application link for a Room.
        GET / POST /api/recruitment/rooms/{id}/link/
        """
        room = self.get_object()

        # If room does not have a token yet, generate one
        if not room.share_token:
            room.share_token = generate_secure_share_token()
            room.save(update_fields=['share_token', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Shareable link retrieved successfully.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/deactivate')
    def deactivate_link(self, request, pk=None):
        """
        US-21-T5: Deactivate shareable link, immediately invalidating candidate access.
        POST /api/recruitment/rooms/{id}/link/deactivate/
        """
        room = self.get_object()
        room.link_is_active = False
        room.save(update_fields=['link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been deactivated.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/activate')
    def activate_link(self, request, pk=None):
        """
        US-21-T5: Reactivate an existing shareable link.
        POST /api/recruitment/rooms/{id}/link/activate/
        """
        room = self.get_object()
        room.link_is_active = True
        room.save(update_fields=['link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been activated.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/regenerate')
    def regenerate_link(self, request, pk=None):
        """
        US-21-T5: Regenerate a new cryptographically secure token, immediately
        invalidating the previous token and enabling candidate access.
        POST /api/recruitment/rooms/{id}/link/regenerate/
        """
        room = self.get_object()
        room.share_token = generate_secure_share_token()
        room.link_is_active = True
        room.save(update_fields=['share_token', 'link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been regenerated with a new secure token.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )


class PublicApplicationView(APIView):
    """
    US-21-T3: Public Unauthenticated Endpoint for Candidate Application Link Resolution.
    GET /api/recruitment/apply/{token}/
    
    Verifies token validity, expiration, and active status.
    Returns opening details, requirements, and score weighting if active.
    Returns HTTP 410 Gone if deactivated or expired.
    Returns HTTP 404 Not Found if token does not exist.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        is_valid, room, error_message, status_code = validate_share_token(token)

        if not is_valid:
            if status_code == 404:
                error_code = "LINK_NOT_FOUND"
            elif room and room.status == 'CLOSED':
                error_code = "ROOM_CLOSED"
            elif room and is_token_expired(room):
                error_code = "LINK_EXPIRED"
            else:
                error_code = "LINK_DEACTIVATED"
            return Response(
                {
                    "error": error_message,
                    "code": error_code,
                    "is_active": False,
                    "room_title": room.title if room else None,
                    "company_name": room.company_name if room else None,
                },
                status=status_code
            )

        serializer = PublicRoomDetailsSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


