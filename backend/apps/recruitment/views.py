from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import RecruitmentRoom
from .serializers import RecruitmentRoomSerializer
from .permissions import IsHRManager, IsRoomOwner


class RecruitmentRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD API for HR Recruitment Rooms (US-18).
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
