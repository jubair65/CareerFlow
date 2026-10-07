from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RecruitmentRoom
from .serializers import RecruitmentRoomSerializer, RoomRequirementsSerializer
from .permissions import IsHRManager, IsRoomOwner
from .services.matcher_bridge import sync_room_to_job_requirement


class RecruitmentRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD API for HR Recruitment Rooms (US-18 & US-19).
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
