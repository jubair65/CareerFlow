import os
import mimetypes
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import DataAccessLog, Notification, AIConsentLog
from .serializers import (
    NotificationSerializer,
    AIConsentLogSerializer,
    AIConsentSubmitSerializer,
    AI_BIOMETRIC_POLICY_V1,
)
from apps.authentication.models import User
from apps.authentication.permissions import IsHRManager, IsAgencyAdmin


class QueryParamJWTAuthentication(JWTAuthentication):
    """
    Allows JWT authentication via 'token' query parameter in addition to the
    standard 'Authorization: Bearer <token>' header. This is essential for browser
    direct links (e.g., <a target="_blank"> or window.open) for viewing/downloading files.
    """
    def authenticate(self, request):
        # 1. Try standard Authorization header first
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated_token = self.get_validated_token(raw_token)
                return self.get_user(validated_token), validated_token

        # 2. Try query parameter 'token' (handles both HttpRequest and DRF Request)
        query_token = request.GET.get('token') or getattr(request, 'query_params', {}).get('token')
        if query_token:
            validated_token = self.get_validated_token(query_token)
            return self.get_user(validated_token), validated_token

        return None


class DataAccessLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = DataAccessLog
        fields = ['id', 'user_email', 'user_role', 'resource_path', 'action', 'status', 'ip_address', 'timestamp']


class SecureFileServeView(APIView):
    authentication_classes = [QueryParamJWTAuthentication, JWTAuthentication]
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

        content_type, _ = mimetypes.guess_type(str(target_path))
        response = FileResponse(open(target_path, 'rb'), content_type=content_type or 'application/octet-stream')
        if target_path.suffix.lower() == '.pdf':
            response['Content-Disposition'] = f'inline; filename="{target_path.name}"'
        else:
            response['Content-Disposition'] = f'attachment; filename="{target_path.name}"'
        return response


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


# ==============================================================================
# US-34: In-app Notification Views
# ==============================================================================

class NotificationListView(APIView):
    """
    US-34-T5: Retrieve list of notifications and unread count for authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(user=request.user)
        unread_count = queryset.filter(is_read=False).count()
        notifications = queryset[:50]
        serializer = NotificationSerializer(notifications, many=True)
        return Response({
            'unread_count': unread_count,
            'notifications': serializer.data,
        }, status=status.HTTP_200_OK)


class NotificationMarkReadView(APIView):
    """
    US-34-T5: Mark a single notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = Notification.objects.filter(id=pk, user=request.user).first()
        if not notification:
            return Response(
                {'error': f'Notification with id {pk} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = NotificationSerializer(notification)
        return Response({
            'message': 'Notification marked as read.',
            'notification': serializer.data
        }, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """
    US-34-T5: Mark all unread notifications for authenticated user as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({
            'message': f'Marked {updated_count} notification(s) as read.',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)


class NotificationDetailView(APIView):
    """
    US-34-T5: Delete a notification belonging to the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        notification = Notification.objects.filter(id=pk, user=request.user).first()
        if not notification:
            return Response(
                {'error': f'Notification with id {pk} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.delete()
        return Response({'message': 'Notification deleted successfully.'}, status=status.HTTP_200_OK)


# ============================================================================
# US-48: AI Biometric & Evaluation Consent Notice Gatekeeper
# ============================================================================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def verify_ai_consent(request, user=None, email=None) -> bool:
    """
    US-48-T5: Backend check verifying explicit AI consent before initiating
    audio/video presentation telemetry or downstream AI scoring pipelines.
    """
    # 1. Token Check
    token = (
        request.headers.get('X-AI-Consent-Token')
        or request.data.get('consent_token')
        or getattr(request, 'query_params', {}).get('consent_token')
        or request.GET.get('consent_token')
    )
    if token:
        if AIConsentLog.objects.filter(consent_token=token, agreed=True).exists():
            return True

    # 2. Authenticated User Check
    effective_user = user or (request.user if getattr(request, 'user', None) and request.user.is_authenticated else None)
    if effective_user:
        return AIConsentLog.objects.filter(user=effective_user, agreed=True).exists()

    # 3. Candidate Email Check
    effective_email = email or request.data.get('email')
    if effective_email:
        return AIConsentLog.objects.filter(email=effective_email, agreed=True).exists()

    return False


class AIConsentRecordView(APIView):
    """
    US-48-T2: Record candidate consent decision (agreement or refusal)
    with timestamp, policy version, IP address, and user agent.
    POST /api/core/ai-consent/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AIConsentSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        agreed = serializer.validated_data['agreed']
        policy_version = serializer.validated_data.get('policy_version', 'v1.0')
        consent_type = serializer.validated_data.get('consent_type', AIConsentLog.ConsentType.BIOMETRIC_EVALUATION)
        email = serializer.validated_data.get('email', '')

        # Resolve user
        user = request.user if request.user and request.user.is_authenticated else None
        if not email and user:
            email = user.email

        client_ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        consent_log = AIConsentLog.objects.create(
            user=user,
            email=email,
            consent_type=consent_type,
            policy_version=policy_version,
            agreed=agreed,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        if not agreed:
            return Response({
                'status': 'refused',
                'agreed': False,
                'message': 'AI Biometric and Evaluation Consent was declined. Video capture and evaluation remain locked.',
                'policy_version': policy_version,
                'consent_token': consent_log.consent_token,
                'timestamp': consent_log.timestamp,
            }, status=status.HTTP_200_OK)

        return Response({
            'status': 'recorded',
            'agreed': True,
            'message': 'AI Biometric Analysis and Evaluation consent successfully recorded.',
            'policy_version': policy_version,
            'consent_token': consent_log.consent_token,
            'timestamp': consent_log.timestamp,
        }, status=status.HTTP_201_CREATED)


class AIConsentStatusView(APIView):
    """
    US-48-T2: Check whether current user/token/IP has valid active consent.
    GET /api/core/ai-consent/status/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        has_consented = verify_ai_consent(request)
        token = (
            request.headers.get('X-AI-Consent-Token')
            or getattr(request, 'query_params', {}).get('consent_token')
            or request.GET.get('consent_token')
        )
        active_log = None
        if token:
            active_log = AIConsentLog.objects.filter(consent_token=token, agreed=True).first()
        elif request.user and request.user.is_authenticated:
            active_log = AIConsentLog.objects.filter(user=request.user, agreed=True).first()

        return Response({
            'has_consented': has_consented,
            'policy_version': active_log.policy_version if active_log else 'v1.0',
            'consent_token': active_log.consent_token if active_log else None,
            'consented_at': active_log.timestamp if active_log else None,
        }, status=status.HTTP_200_OK)


class AIConsentPolicyView(APIView):
    """
    US-48-T1: Retrieve the structured AI Biometric and Evaluation Privacy Notice.
    GET /api/core/ai-consent/policy/
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(AI_BIOMETRIC_POLICY_V1, status=status.HTTP_200_OK)
