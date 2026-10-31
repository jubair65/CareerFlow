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
    PracticeSessionRenameSerializer,
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
from .permissions import IsVideoOwner

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
    US-16-T2 & US-16-T5:
    GET /api/presentation/history/
    Returns the chronologically ordered list (newest first) of previous presentation
    video analyses for the authenticated student.
    Enforces strict tenant isolation and uses select_related/prefetch_related for high performance (<1.2s).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        videos = PresentationVideo.objects.filter(
            user=request.user
        ).select_related(
            'speech_analysis',
            'behavioral_analysis',
            'presentation_score',
            'ai_feedback'
        ).prefetch_related(
            'execution_logs'
        ).order_by('-uploaded_at')

        status_filter = request.query_params.get('status')
        if status_filter:
            videos = videos.filter(status=status_filter.upper())

        search_query = request.query_params.get('search')
        if search_query:
            videos = videos.filter(original_filename__icontains=search_query)

        serializer = PresentationVideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PresentationScoreTrendsView(APIView):
    """
    US-17-T2 & US-17-T5:
    GET /api/presentation/trends/
    Aggregates composite and category scores across chronological attempts
    for the authenticated student.
    Enforces strict tenant isolation (student only sees their own attempts)
    and computes progress deltas, category comparisons, and streak metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        videos = PresentationVideo.objects.filter(
            user=request.user,
            presentation_score__isnull=False
        ).select_related(
            'presentation_score',
            'speech_analysis',
            'behavioral_analysis'
        ).order_by('uploaded_at')

        total_attempts = videos.count()

        if total_attempts == 0:
            return Response({
                'total_attempts': 0,
                'trend_points': [],
                'improvements': {
                    'overall_delta': '+0%',
                    'speech_delta': '+0%',
                    'behavioral_delta': '+0%',
                    'pace_delta': '+0%',
                    'eye_contact_delta': '+0%',
                    'overall_diff_points': 0,
                    'speech_diff_points': 0,
                    'behavioral_diff_points': 0,
                },
                'summary': {
                    'total_attempts': 0,
                    'latest_score': None,
                    'highest_score': None,
                    'lowest_score': None,
                    'average_score': None,
                    'first_score': None,
                    'progress_status': 'NO_DATA',
                },
                'highlights': [],
                'message': 'Upload your first video to start tracking presentation progress.'
            }, status=status.HTTP_200_OK)

        trend_points = []
        overall_scores = []

        for idx, video in enumerate(videos, start=1):
            score = video.presentation_score
            speech = getattr(video, 'speech_analysis', None)
            behavioral = getattr(video, 'behavioral_analysis', None)

            overall_scores.append(score.overall_score)

            trend_points.append({
                'attempt': idx,
                'video_id': video.id,
                'original_filename': video.original_filename,
                'date': video.uploaded_at.strftime('%Y-%m-%d'),
                'formatted_date': video.uploaded_at.strftime('%b %d, %Y'),
                'timestamp': video.uploaded_at.isoformat(),
                'duration_seconds': video.duration_seconds,
                'overall': score.overall_score,
                'overall_score': score.overall_score,
                'speech': score.speech_score,
                'speech_score': score.speech_score,
                'behavioral': score.behavioral_score,
                'behavioral_score': score.behavioral_score,
                'pace': score.pace_score,
                'pace_score': score.pace_score,
                'filler': score.filler_score,
                'filler_score': score.filler_score,
                'eye_contact': score.eye_contact_score,
                'eye_contact_score': score.eye_contact_score,
                'posture': score.posture_score,
                'posture_score': score.posture_score,
                'engagement': score.engagement_score,
                'engagement_score': score.engagement_score,
                'grade_label': score.grade_label,
                'words_per_minute': speech.words_per_minute if speech else None,
                'filler_word_count': speech.filler_word_count if speech else None,
                'clarity_score': speech.clarity_score if speech else None,
            })

        first_point = trend_points[0]
        latest_point = trend_points[-1]

        def calculate_delta(latest_val, first_val):
            diff = latest_val - first_val
            prefix = "+" if diff > 0 else ""
            return f"{prefix}{diff}%"

        overall_delta_str = calculate_delta(latest_point['overall'], first_point['overall'])
        speech_delta_str = calculate_delta(latest_point['speech'], first_point['speech'])
        behavioral_delta_str = calculate_delta(latest_point['behavioral'], first_point['behavioral'])
        pace_delta_str = calculate_delta(latest_point['pace'], first_point['pace'])
        eye_contact_delta_str = calculate_delta(latest_point['eye_contact'], first_point['eye_contact'])

        improvements = {
            'overall_delta': overall_delta_str,
            'speech_delta': speech_delta_str,
            'behavioral_delta': behavioral_delta_str,
            'pace_delta': pace_delta_str,
            'eye_contact_delta': eye_contact_delta_str,
            'overall_diff_points': latest_point['overall'] - first_point['overall'],
            'speech_diff_points': latest_point['speech'] - first_point['speech'],
            'behavioral_diff_points': latest_point['behavioral'] - first_point['behavioral'],
        }

        highlights = []
        if total_attempts >= 2:
            eye_diff = latest_point['eye_contact'] - first_point['eye_contact']
            if eye_diff > 0:
                highlights.append(f"Eye contact improved by +{eye_diff}% since Attempt 1")
            elif eye_diff < 0:
                highlights.append(f"Eye contact adjusted by {eye_diff}% since Attempt 1")

            speech_diff = latest_point['speech'] - first_point['speech']
            if speech_diff > 0:
                highlights.append(f"Vocal delivery and pacing score improved by +{speech_diff}% since Attempt 1")

            overall_diff = latest_point['overall'] - first_point['overall']
            if overall_diff > 0:
                highlights.append(f"Overall presentation score improved by +{overall_diff}% across {total_attempts} attempts")
            elif overall_diff == 0:
                highlights.append("Overall presentation score remained steady with consistent delivery")
            else:
                highlights.append(f"Overall presentation score shifted by {overall_diff}% since baseline")
        else:
            highlights.append("Initial baseline attempt registered. Complete a second take to visualize your improvement trajectory!")

        avg_score = round(sum(overall_scores) / len(overall_scores), 1)

        summary = {
            'total_attempts': total_attempts,
            'latest_score': latest_point['overall'],
            'highest_score': max(overall_scores),
            'lowest_score': min(overall_scores),
            'average_score': avg_score,
            'first_score': first_point['overall'],
            'progress_status': 'BASELINE' if total_attempts == 1 else (
                'IMPROVED' if latest_point['overall'] > first_point['overall'] else (
                    'DECLINED' if latest_point['overall'] < first_point['overall'] else 'STABLE'
                )
            ),
        }

        return Response({
            'total_attempts': total_attempts,
            'trend_points': trend_points,
            'improvements': improvements,
            'summary': summary,
            'highlights': highlights,
            'message': (
                "Upload a second attempt to see your improvement curve!"
                if total_attempts == 1
                else "Score trends aggregated successfully."
            )
        }, status=status.HTTP_200_OK)


class PresentationVideoDetailView(APIView):
    """
    US-16-T4 & US-16-T5:
    GET /api/presentation/<pk>/ or /api/presentation/history/<pk>/
    DELETE /api/presentation/<pk>/
    View complete analysis details or delete a presentation video.
    Strictly verifies ownership to prevent unauthorized access (tenant isolation).
    """
    permission_classes = [permissions.IsAuthenticated, IsVideoOwner]

    def get_object(self, pk):
        return PresentationVideo.objects.filter(pk=pk).select_related(
            'speech_analysis',
            'behavioral_analysis',
            'presentation_score',
            'ai_feedback'
        ).prefetch_related(
            'execution_logs'
        ).first()

    def get(self, request, pk):
        video = self.get_object(pk)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        if video.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to access this presentation analysis.'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.check_object_permissions(request, video)
        serializer = PresentationVideoSerializer(video, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        video = self.get_object(pk)
        if not video:
            return Response({'error': 'Video not found.'}, status=status.HTTP_404_NOT_FOUND)

        if video.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to delete this presentation video.'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.check_object_permissions(request, video)

        # US-44-T3: Safely remove physical video file from media storage
        if video.file:
            try:
                if hasattr(video.file, 'path') and os.path.exists(video.file.path):
                    os.remove(video.file.path)
                elif hasattr(video.file, 'storage') and video.file.name:
                    video.file.storage.delete(video.file.name)
            except (OSError, ValueError):
                pass

        deleted_id = video.id
        video.delete()
        return Response({
            'message': 'Presentation video deleted successfully.',
            'deleted_id': deleted_id
        }, status=status.HTTP_200_OK)


class PracticeSessionRenameView(APIView):
    """
    US-44-T2:
    PATCH /api/presentation/<pk>/rename/
    PATCH /api/practice/<pk>/rename/
    Rename a practice session recording attempt with a custom title or tag (max 100 chars).
    Strictly verifies ownership to prevent unauthorized cross-user modifications.
    """
    permission_classes = [permissions.IsAuthenticated, IsVideoOwner]

    def get_object(self, pk):
        return PresentationVideo.objects.filter(pk=pk).select_related(
            'speech_analysis',
            'behavioral_analysis',
            'presentation_score',
            'ai_feedback'
        ).first()

    def patch(self, request, pk):
        video = self.get_object(pk)
        if not video:
            return Response({'error': 'Practice session not found.'}, status=status.HTTP_404_NOT_FOUND)

        if video.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to rename this practice session.'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.check_object_permissions(request, video)

        serializer = PracticeSessionRenameSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video.title = serializer.validated_data['title']
        video.save(update_fields=['title'])

        return Response({
            'message': 'Practice session renamed successfully.',
            'video': PresentationVideoSerializer(video, context={'request': request}).data
        }, status=status.HTTP_200_OK)



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
            # US-34: Generate notification upon Presentation score calculation
            try:
                from apps.core.services.notification_service import NotificationService
                NotificationService.notify_presentation_analysis_complete(
                    user=video.user,
                    video=video,
                    overall_score=getattr(score, 'overall_score', None)
                )
            except Exception as notif_err:
                logger.warning(f"[US-34] Notification generation failed: {notif_err}")

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

