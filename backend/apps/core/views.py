import os
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DataAccessLog
from apps.authentication.models import User
from apps.authentication.permissions import IsHRManager, IsAgencyAdmin


class DataAccessLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DataAccessLog
        fields = ['id', 'user_email', 'user_role', 'resource_path', 'action', 'status', 'ip_address', 'timestamp']


class SecureFileServeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def get(self, request, file_path):
        user = request.user
        ip = self.get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')

        is_authorized = False
        if user.role in [User.Role.AGENCY_ADMIN, User.Role.HR_MANAGER]:
            is_authorized = True
        elif user.role == User.Role.STUDENT:
            user_prefix = str(user.id)
            if file_path.startswith(f"students/{user_prefix}/") or file_path.startswith(f"{user_prefix}/"):
                is_authorized = True

        DataAccessLog.objects.create(
            user=user,
            resource_path=file_path,
            action=DataAccessLog.Action.DOWNLOAD,
            status=DataAccessLog.Status.GRANTED if is_authorized else DataAccessLog.Status.DENIED,
            ip_address=ip,
            user_agent=ua
        )

        if not is_authorized:
            return Response({
                'error': 'Access denied: You do not have permission to access this candidate file.'
            }, status=status.HTTP_403_FORBIDDEN)

        media_root = Path(settings.MEDIA_ROOT).resolve()
        target_path = (media_root / file_path).resolve()

        if not str(target_path).startswith(str(media_root)):
            return Response({'error': 'Invalid file path.'}, status=status.HTTP_400_BAD_REQUEST)

        if not target_path.exists() or not target_path.is_file():
            return Response({'error': 'File not found.'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(open(target_path, 'rb'))


class AuditLogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in [User.Role.HR_MANAGER, User.Role.AGENCY_ADMIN]:
            return Response({
                'error': 'Access denied: Only HR Managers and Agency Admins can inspect audit logs.'
            }, status=status.HTTP_403_FORBIDDEN)

        logs = DataAccessLog.objects.all().select_related('user')[:50]
        serializer = DataAccessLogSerializer(logs, many=True)
        return Response({
            'total_logs': DataAccessLog.objects.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
