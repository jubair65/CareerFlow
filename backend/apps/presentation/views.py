import os
import logging
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import (
    PresentationVideo,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationScore,
    PresentationFeedback,
    PipelineExecutionLog,
)
from .serializers import (
    PresentationVideoSerializer,
    VideoUploadSerializer,
    SpeechAnalysisSerializer,
    BehavioralAnalysisSerializer,
    PresentationScoreSerializer,
    PresentationFeedbackSerializer,
    PipelineExecutionLogSerializer,
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
from .services.behavioral_analyzer import analyze_behavior
from .services.scorer import calculate_presentation_score
from .services.llm_coach_service import GeminiPresentationCoachService
from .services.pipeline_manager import PipelineManager
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


class PresentationBehavioralAnalysisView(APIView):
    """
    GET /api/presentation/<video_id>/behavioral/
    POST /api/presentation/<video_id>/behavioral/
    Retrieve or trigger behavioral analysis (eye contact, posture, engagement)
    for a candidate's presentation video (US-13).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_video(self, video_id, user):
        return PresentationVideo.objects.filter(id=video_id, user=user).first()

    def get(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        behavioral_analysis = getattr(video, 'behavioral_analysis', None)
        if not behavioral_analysis:
            return Response(
                {
                    'detail': 'Behavioral analysis has not been performed on this video yet.',
                    'status': video.status
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BehavioralAnalysisSerializer(behavioral_analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            behavioral_record = analyze_behavior(video)
            serializer = BehavioralAnalysisSerializer(behavioral_record)
            return Response(
                {
                    'message': 'Behavioral analysis completed successfully.',
                    'behavioral_analysis': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error analyzing behavior for video {video_id}: {e}")
            return Response(
                {'error': f"Behavioral analysis failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PresentationScoreView(APIView):
    """
    GET /api/presentation/<video_id>/score/
    POST /api/presentation/<video_id>/score/
    Retrieve or calculate composite presentation score synthesizing speech and behavioral metrics (US-14).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_video(self, video_id, user):
        return PresentationVideo.objects.filter(id=video_id, user=user).first()

    def _ensure_analysis_and_score(self, video, force_refresh: bool = False):
        # 1. Run speech analysis if missing or force_refresh
        has_speech = hasattr(video, 'speech_analysis') and video.speech_analysis is not None
        if not has_speech or force_refresh:
            try:
                analyze_speech(video)
                video.refresh_from_db()
            except Exception as e:
                logger.warning(f"Could not automatically execute speech analysis on video {video.id}: {e}")

        # 2. Run behavioral analysis if missing, force_refresh, or previous analysis had old degraded fallback metrics (0, 75, 75)
        has_beh = hasattr(video, 'behavioral_analysis') and video.behavioral_analysis is not None
        is_dummy_beh = False
        if has_beh:
            b = video.behavioral_analysis
            is_dummy_beh = (b.eye_contact_score == 0 and b.posture_score == 75 and b.engagement_score == 75)

        if not has_beh or force_refresh or is_dummy_beh:
            try:
                analyze_behavior(video)
                video.refresh_from_db()
            except Exception as e:
                logger.warning(f"Could not automatically execute behavioral analysis on video {video.id}: {e}")

        # 3. Calculate score
        return calculate_presentation_score(video)

    def get(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        score = getattr(video, 'presentation_score', None)
        # Check if score needs calculation or refresh from old dummy metrics
        beh = getattr(video, 'behavioral_analysis', None)
        is_dummy = beh and (beh.eye_contact_score == 0 and beh.posture_score == 75 and beh.engagement_score == 75)

        if not score or score.overall_score == 0 or is_dummy:
            score = self._ensure_analysis_and_score(video, force_refresh=bool(is_dummy))

        serializer = PresentationScoreSerializer(score)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            force = request.data.get('force', True) if isinstance(request.data, dict) else True
            score = self._ensure_analysis_and_score(video, force_refresh=force)
            serializer = PresentationScoreSerializer(score)
            return Response(
                {
                    'message': 'Presentation score calculated successfully.',
                    'presentation_score': serializer.data
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error calculating score for video {video_id}: {e}")
            return Response(
                {'error': f"Score calculation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PresentationSuggestionsView(APIView):
    """
    GET /api/presentation/<video_id>/suggestions/
    POST /api/presentation/<video_id>/suggestions/
    POST /api/presentation/<video_id>/suggestions/generate/
    Retrieve or generate personalized AI improvement suggestions (US-15)
    using GeminiPresentationCoachService with structured JSON output and drill callouts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_video(self, video_id, user):
        return PresentationVideo.objects.filter(id=video_id, user=user).first()

    def _generate_or_get_feedback(self, video, force_refresh: bool = False):
        if not force_refresh:
            existing = PresentationFeedback.objects.filter(video=video).first()
            if existing:
                return existing

        speech = getattr(video, 'speech_analysis', None)
        behavioral = getattr(video, 'behavioral_analysis', None)
        score = getattr(video, 'presentation_score', None)

        if not speech:
            try:
                speech = analyze_speech(video)
                video.refresh_from_db()
            except Exception as e:
                logger.warning(f"Speech analysis failed while preparing suggestions: {e}")

        if not behavioral:
            try:
                behavioral = analyze_behavior(video)
                video.refresh_from_db()
            except Exception as e:
                logger.warning(f"Behavioral analysis failed while preparing suggestions: {e}")

        if not score:
            try:
                score = calculate_presentation_score(video)
                video.refresh_from_db()
            except Exception as e:
                logger.warning(f"Score calculation failed while preparing suggestions: {e}")

        metrics = {
            'wpm': getattr(speech, 'words_per_minute', 140.0) if speech else 140.0,
            'filler_count': getattr(speech, 'filler_word_count', 0) if speech else 0,
            'filler_breakdown': getattr(speech, 'filler_words_breakdown', {}) if speech else {},
            'transcript': getattr(speech, 'transcript', '') if speech else '',
            'eye_contact': getattr(behavioral, 'eye_contact_score', 75) if behavioral else 75,
            'posture_score': getattr(behavioral, 'posture_score', 80) if behavioral else 80,
            'engagement_score': getattr(behavioral, 'engagement_score', 75) if behavioral else 75,
            'overall_score': getattr(score, 'overall_score', 78) if score else 78,
            'pace_score': getattr(score, 'pace_score', 80) if score else 80,
            'filler_score': getattr(score, 'filler_score', 85) if score else 85,
            'eye_contact_score': getattr(score, 'eye_contact_score', getattr(behavioral, 'eye_contact_score', 75)) if (score or behavioral) else 75,
            'speech_score': getattr(score, 'speech_score', 75) if score else 75,
            'behavioral_score': getattr(score, 'behavioral_score', 75) if score else 75,
            'duration_seconds': getattr(video, 'duration_seconds', getattr(speech, 'duration_seconds', 0.0)) if (video or speech) else 0.0,
        }

        service = GeminiPresentationCoachService()
        feedback_data = service.generate_feedback(metrics)

        feedback, _ = PresentationFeedback.objects.update_or_create(
            video=video,
            defaults={
                'summary': feedback_data.get('summary', 'Solid presentation foundation.'),
                'strengths': feedback_data.get('strengths', []),
                'improvements': feedback_data.get('critical_improvements', []),
                'practice_tip': feedback_data.get('practice_script_tip', ''),
            }
        )
        return feedback

    def get(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        feedback = self._generate_or_get_feedback(video, force_refresh=False)
        serializer = PresentationFeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, video_id):
        video = self.get_video(video_id, request.user)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            feedback = self._generate_or_get_feedback(video, force_refresh=True)
            serializer = PresentationFeedbackSerializer(feedback)
            return Response(
                {
                    'message': 'AI coaching suggestions generated successfully.',
                    'ai_feedback': serializer.data,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating suggestions for video {video_id}: {e}")
            return Response(
                {'error': f"Failed to generate feedback: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PipelineRetryView(APIView):
    """
    POST /api/presentation/<video_id>/retry/
    US-40: Manually triggers supervised pipeline retry for a presentation video.
    Re-runs speech, behavioral, scoring, and suggestions with exponential backoff
    and graceful degradation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, video_id):
        video = PresentationVideo.objects.filter(id=video_id, user=request.user).first()
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            pipeline_result = PipelineManager.retry_pipeline(video)
            video.refresh_from_db()
            serializer = PresentationVideoSerializer(video, context={'request': request})
            return Response(
                {
                    'message': 'Pipeline execution initiated / completed.',
                    'result': pipeline_result,
                    'video': serializer.data,
                },
                status=status.HTTP_200_OK if pipeline_result.get('success') else status.HTTP_207_MULTI_STATUS
            )
        except Exception as e:
            logger.error(f"[US-40] Error retrying pipeline for video {video_id}: {e}", exc_info=True)
            return Response(
                {'error': f"Pipeline retry failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PipelineStatusView(APIView):
    """
    GET /api/presentation/<video_id>/status/
    US-40: Returns real-time pipeline status, degradation indicators, and recent stage logs.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, video_id):
        video = PresentationVideo.objects.filter(id=video_id, user=request.user).first()
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        telemetry = PipelineManager.get_pipeline_telemetry(video)
        return Response(telemetry, status=status.HTTP_200_OK)


class PipelineLogsView(APIView):
    """
    GET /api/presentation/<video_id>/logs/
    US-40: Returns chronological execution logs and telemetry for a presentation video.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, video_id):
        video = PresentationVideo.objects.filter(id=video_id, user=request.user).first()
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        logs = video.execution_logs.all()[:50]
        serializer = PipelineExecutionLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

