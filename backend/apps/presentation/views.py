import os
import logging
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import PresentationVideo, SpeechAnalysis
from .serializers import (
    PresentationVideoSerializer,
    VideoUploadSerializer,
    SpeechAnalysisSerializer,
)
from .validators import (
    validate_video_file,
    validate_video_duration,
    probe_video_duration,
    MAX_UPLOAD_SIZE,
    MAX_DURATION_SECONDS
)
from .services.video_compressor import compress_video, cleanup_staging_file
from .services.speech_analyzer import analyze_speech
from apps.core.models import DataAccessLog

logger = logging.getLogger(__name__)


class VideoUploadView(APIView):
    """
    POST /api/presentation/upload/
    Uploads a candidate's presentation video (MP4, WebM, MOV; max 250MB, max 180s).
    Stages the file, runs automatic FFmpeg compression to 720p H.264 (<50MB),
    cleans up the raw staging file, deactivates prior active videos, and registers
    the normalized video ready for downstream AI analysis (US-11).
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No video file uploaded. Please attach a video under the "file" field.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']

        # 1. Validation (File size <= 250MB, allowed extensions)
        try:
            raw_ext = validate_video_file(uploaded_file)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        staging_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(staging_dir, exist_ok=True)
        staging_filename = f"raw_{request.user.id}_{timestamp}.{raw_ext}"
        staging_path = os.path.join(staging_dir, staging_filename)

        # 2. Save raw file to staging path in chunks
        try:
            with open(staging_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
        except Exception as e:
            logger.error(f"Failed to write staging file: {e}")
            cleanup_staging_file(staging_path)
            return Response(
                {'error': 'Server error saving uploaded video staging file.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. Probe and validate duration
        duration = probe_video_duration(staging_path)
        if duration > MAX_DURATION_SECONDS:
            cleanup_staging_file(staging_path)
            return Response(
                {
                    'error': f'Video duration ({duration}s) exceeds the maximum allowed length of {MAX_DURATION_SECONDS}s (3 minutes).'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Target destination for compressed video
        target_rel_dir = f"students/{request.user.id}/videos"
        target_rel_path = f"{target_rel_dir}/{timestamp}_presentation.mp4"
        target_abs_path = os.path.join(settings.MEDIA_ROOT, target_rel_path)

        # 5. Compress video using FFmpeg (720p H.264, CRF 26 -> <50MB)
        compression_result = compress_video(staging_path, target_abs_path)

        # 6. Delete raw staging file immediately to preserve disk space
        cleanup_staging_file(staging_path)

        # 7. Database persistence
        with transaction.atomic():
            # Deactivate previous active presentation video
            PresentationVideo.objects.filter(user=request.user, is_active=True).update(is_active=False)

            compressed_size = compression_result.get('compressed_size', uploaded_file.size)

            video_record = PresentationVideo.objects.create(
                user=request.user,
                file=target_rel_path,
                original_filename=uploaded_file.name,
                raw_file_size=uploaded_file.size,
                compressed_file_size=compressed_size,
                file_type='mp4',
                duration_seconds=duration,
                is_active=True,
                status='READY_FOR_ANALYSIS'
            )

            # Audit logging
            DataAccessLog.objects.create(
                user=request.user,
                resource_path=target_rel_path,
                action=DataAccessLog.Action.UPLOAD,
                status=DataAccessLog.Status.GRANTED,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

        serializer = PresentationVideoSerializer(video_record, context={'request': request})
        return Response(
            {
                'message': 'Presentation video uploaded, compressed, and registered successfully.',
                'video': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class CurrentPresentationVideoView(APIView):
    """
    GET /api/presentation/active/
    Returns the candidate's currently active presentation video.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_video = PresentationVideo.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not active_video:
            return Response(
                {'detail': 'No active presentation video found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PresentationVideoSerializer(active_video, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PresentationVideoHistoryView(APIView):
    """
    GET /api/presentation/history/
    Returns the list of presentation videos uploaded/recorded by the candidate.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        videos = PresentationVideo.objects.filter(user=request.user)
        serializer = PresentationVideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PresentationVideoDetailView(APIView):
    """
    GET /api/presentation/<pk>/
    DELETE /api/presentation/<pk>/
    View details or delete a presentation video.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        return PresentationVideo.objects.filter(pk=pk, user=user).first()

    def get(self, request, pk):
        video = self.get_object(pk, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PresentationVideoSerializer(video, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        video = self.get_object(pk, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Remove physical file if exists
        if video.file and os.path.exists(video.file.path):
            try:
                os.remove(video.file.path)
            except OSError:
                pass

        video.delete()
        return Response({'message': 'Presentation video deleted successfully.'}, status=status.HTTP_200_OK)


class PresentationSpeechAnalysisView(APIView):
    """
    GET /api/presentation/<video_id>/speech/
    POST /api/presentation/<video_id>/speech/
    Retrieve or trigger speech analysis for a candidate's presentation video (US-12).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_video(self, video_id, user):
        return PresentationVideo.objects.filter(id=video_id, user=user).first()

    def get(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        speech_analysis = getattr(video, 'speech_analysis', None)
        if not speech_analysis:
            return Response(
                {
                    'detail': 'Speech analysis has not been performed on this video yet.',
                    'status': video.status
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SpeechAnalysisSerializer(speech_analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            speech_record = analyze_speech(video)
            serializer = SpeechAnalysisSerializer(speech_record)
            return Response(
                {
                    'message': 'Speech analysis completed successfully.',
                    'speech_analysis': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error analyzing speech for video {video_id}: {e}")
            return Response(
                {'error': f"Speech analysis failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
