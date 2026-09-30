import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type

from django.db import transaction
from django.utils import timezone

from apps.presentation.models import (
    PresentationVideo,
    SpeechAnalysis,
    BehavioralAnalysis,
    PresentationScore,
    PresentationFeedback,
    PipelineExecutionLog,
)
from apps.presentation.services.speech_analyzer import analyze_speech
from apps.presentation.services.behavioral_analyzer import analyze_behavior
from apps.presentation.services.scorer import calculate_presentation_score
from apps.presentation.services.llm_coach_service import GeminiPresentationCoachService

logger = logging.getLogger(__name__)


# Non-retryable error classes (fatal data/media issues where retry won't fix the problem)
NON_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    FileNotFoundError,
    ValueError,
    TypeError,
    AssertionError,
)


def retry_with_backoff(
    stage: str,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    non_retryable: Tuple[Type[Exception], ...] = NON_RETRYABLE_EXCEPTIONS,
):
    """
    Decorator for AI pipeline stages implementing exponential backoff with jitter (US-40).
    Captures stage duration and logs attempts to PipelineExecutionLog.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract video instance from args/kwargs if present for log persistence
            video = None
            for arg in args:
                if isinstance(arg, PresentationVideo):
                    video = arg
                    break
            if not video and 'video' in kwargs:
                video = kwargs['video']

            last_exception = None

            for attempt in range(1, max_attempts + 1):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                    if video:
                        try:
                            PipelineExecutionLog.objects.create(
                                video=video,
                                stage=stage,
                                status=PipelineExecutionLog.Status.SUCCESS,
                                attempt=attempt,
                                execution_time_ms=elapsed_ms,
                                details={'function': func.__name__}
                            )
                        except Exception as log_err:
                            logger.warning(f"Could not persist PipelineExecutionLog: {log_err}")

                    return result

                except Exception as exc:
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    last_exception = exc
                    error_msg = str(exc)

                    # Check if error is non-retryable
                    is_fatal = isinstance(exc, non_retryable)

                    if is_fatal or attempt >= max_attempts:
                        status = PipelineExecutionLog.Status.FAILED
                        logger.error(
                            f"[US-40] Pipeline stage '{stage}' failed permanently on attempt {attempt}/{max_attempts}: {error_msg}"
                        )
                        if video:
                            try:
                                PipelineExecutionLog.objects.create(
                                    video=video,
                                    stage=stage,
                                    status=status,
                                    attempt=attempt,
                                    error_message=error_msg,
                                    execution_time_ms=elapsed_ms,
                                    details={'function': func.__name__, 'fatal': is_fatal}
                                )
                            except Exception as log_err:
                                logger.warning(f"Could not persist PipelineExecutionLog: {log_err}")
                        raise

                    # Transient retryable error: log RETRY state and sleep
                    logger.warning(
                        f"[US-40] Pipeline stage '{stage}' transient failure (attempt {attempt}/{max_attempts}): {error_msg}. Retrying..."
                    )
                    if video:
                        try:
                            PipelineExecutionLog.objects.create(
                                video=video,
                                stage=stage,
                                status=PipelineExecutionLog.Status.RETRY,
                                attempt=attempt,
                                error_message=error_msg,
                                execution_time_ms=elapsed_ms,
                                details={'function': func.__name__}
                            )
                        except Exception as log_err:
                            logger.warning(f"Could not persist PipelineExecutionLog: {log_err}")

                    # Calculate exponential delay with jitter
                    delay = min(max_delay, base_delay * (backoff_factor ** (attempt - 1)))
                    if jitter:
                        delay += random.uniform(0, 0.3)

                    time.sleep(delay)

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class PipelineManager:
    """
    US-40: Central Pipeline Supervisor and Resilience Manager.
    Orchestrates the multi-stage Presentation AI analysis pipeline:
      1. Speech Analysis (Whisper Speech-to-Text & WPM)
      2. Behavioral Analysis (MediaPipe Face Mesh & Pose) with Graceful Degradation
      3. Presentation Scoring (Adaptive formula based on available telemetry)
      4. AI Coaching Suggestions (Gemini LLM with rule-based fallback)
    """

    @classmethod
    @retry_with_backoff(stage=PipelineExecutionLog.Stage.SPEECH_ANALYSIS, max_attempts=3, base_delay=0.5)
    def execute_speech_analysis(cls, video: PresentationVideo) -> SpeechAnalysis:
        """Executes speech analysis with retry supervisor."""
        return analyze_speech(video)

    @classmethod
    @retry_with_backoff(stage=PipelineExecutionLog.Stage.VISION_ANALYSIS, max_attempts=2, base_delay=0.5)
    def execute_behavioral_analysis(cls, video: PresentationVideo) -> BehavioralAnalysis:
        """Executes computer vision behavioral analysis with retry supervisor."""
        return analyze_behavior(video)

    @classmethod
    @retry_with_backoff(stage=PipelineExecutionLog.Stage.SCORING, max_attempts=2, base_delay=0.3)
    def execute_scoring(cls, video: PresentationVideo) -> PresentationScore:
        """Calculates adaptive composite presentation score."""
        return calculate_presentation_score(video)

    @classmethod
    @retry_with_backoff(stage=PipelineExecutionLog.Stage.SUGGESTIONS, max_attempts=2, base_delay=0.5)
    def execute_suggestions(cls, video: PresentationVideo) -> PresentationFeedback:
        """Generates AI coaching suggestions and actionable drills."""
        speech = getattr(video, 'speech_analysis', None)
        behavioral = getattr(video, 'behavioral_analysis', None)
        score = getattr(video, 'presentation_score', None)

        metrics = {
            'wpm': getattr(speech, 'words_per_minute', 140.0) if speech else 140.0,
            'filler_count': getattr(speech, 'filler_word_count', 0) if speech else 0,
            'filler_breakdown': getattr(speech, 'filler_words_breakdown', {}) if speech else {},
            'eye_contact': getattr(behavioral, 'eye_contact_score', 75) if behavioral else 75,
            'posture_score': getattr(behavioral, 'posture_score', 80) if behavioral else 80,
            'engagement_score': getattr(behavioral, 'engagement_score', 75) if behavioral else 75,
            'overall_score': getattr(score, 'overall_score', 78) if score else 78,
        }

        coach_service = GeminiPresentationCoachService()
        feedback_data = coach_service.generate_feedback(metrics)

        feedback_obj, _ = PresentationFeedback.objects.update_or_create(
            video=video,
            defaults={
                'summary': feedback_data.get('summary', 'Solid presentation foundation.'),
                'strengths': feedback_data.get('strengths', []),
                'improvements': feedback_data.get('critical_improvements', []),
                'practice_tip': feedback_data.get('practice_script_tip', ''),
            }
        )
        return feedback_obj

    @classmethod
    def run_pipeline(cls, video: PresentationVideo, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Executes the end-to-end resilient presentation analysis pipeline (US-40).
        Protects against transient crashes, gracefully degrades on vision tracking failures,
        and records execution logs.
        """
        overall_start = time.perf_counter()
        results: Dict[str, Any] = {
            'success': False,
            'video_id': video.id,
            'status': video.status,
            'stages_completed': [],
            'degraded': False,
            'error': None,
        }

        try:
            # 1. STAGE: SPEECH ANALYSIS
            video.status = 'PROCESSING_SPEECH'
            video.save(update_fields=['status'])

            speech_obj = getattr(video, 'speech_analysis', None)
            if not speech_obj or force_refresh:
                try:
                    speech_obj = cls.execute_speech_analysis(video)
                    video.refresh_from_db()
                except Exception as speech_err:
                    logger.error(f"[US-40] Speech analysis failed fatally for video {video.id}: {speech_err}")
                    video.status = 'FAILED'
                    video.save(update_fields=['status'])
                    results['error'] = f"Speech analysis failed: {str(speech_err)}"
                    results['status'] = 'FAILED'

                    PipelineExecutionLog.objects.create(
                        video=video,
                        stage=PipelineExecutionLog.Stage.PIPELINE,
                        status=PipelineExecutionLog.Status.FAILED,
                        attempt=1,
                        error_message=str(speech_err),
                        execution_time_ms=int((time.perf_counter() - overall_start) * 1000)
                    )
                    return results

            results['stages_completed'].append('speech')

            # 2. STAGE: BEHAVIORAL COMPUTER VISION ANALYSIS (with Graceful Degradation)
            video.status = 'PROCESSING_VISION'
            video.save(update_fields=['status'])

            behavioral_obj = getattr(video, 'behavioral_analysis', None)
            has_behavioral = True

            if not behavioral_obj or force_refresh:
                try:
                    behavioral_obj = cls.execute_behavioral_analysis(video)
                    video.refresh_from_db()
                    results['stages_completed'].append('behavioral')
                except Exception as vision_err:
                    # US-40: Graceful Degradation!
                    # If MediaPipe or OpenCV fails to detect landmarks due to dark lighting or video issues,
                    # DO NOT crash the entire pipeline! Log as DEGRADED and preserve SpeechAnalysis.
                    logger.warning(
                        f"[US-40] Vision analysis degraded for video {video.id}: {vision_err}. Preserving speech data."
                    )
                    has_behavioral = False
                    results['degraded'] = True
                    results['degradation_reason'] = str(vision_err)

                    PipelineExecutionLog.objects.create(
                        video=video,
                        stage=PipelineExecutionLog.Stage.VISION_ANALYSIS,
                        status=PipelineExecutionLog.Status.DEGRADED,
                        attempt=1,
                        error_message=f"Graceful degradation applied: {str(vision_err)}",
                        execution_time_ms=0,
                        details={'fallback': 'Evaluated 100% on speech delivery'}
                    )
            else:
                results['stages_completed'].append('behavioral')

            # 3. STAGE: COMPOSITE SCORING
            video.status = 'SCORING'
            video.save(update_fields=['status'])

            try:
                score_obj = cls.execute_scoring(video)
                video.refresh_from_db()
                results['stages_completed'].append('scoring')
            except Exception as score_err:
                logger.error(f"[US-40] Scoring calculation error: {score_err}")
                # Fallback to direct calculation
                score_obj = calculate_presentation_score(video)
                video.refresh_from_db()
                results['stages_completed'].append('scoring')

            # 4. STAGE: AI COACHING SUGGESTIONS
            try:
                feedback_obj = cls.execute_suggestions(video)
                video.refresh_from_db()
                results['stages_completed'].append('suggestions')
            except Exception as sugg_err:
                logger.warning(f"[US-40] Non-fatal suggestions issue: {sugg_err}")

            # 5. FINAL PIPELINE STATUS
            final_status = 'PARTIALLY_COMPLETED' if (results['degraded'] or not score_obj.has_behavioral_data) else 'COMPLETED'
            video.status = final_status
            video.save(update_fields=['status'])

            elapsed_total_ms = int((time.perf_counter() - overall_start) * 1000)
            PipelineExecutionLog.objects.create(
                video=video,
                stage=PipelineExecutionLog.Stage.PIPELINE,
                status=PipelineExecutionLog.Status.DEGRADED if results['degraded'] else PipelineExecutionLog.Status.SUCCESS,
                attempt=1,
                execution_time_ms=elapsed_total_ms,
                details={'stages': results['stages_completed'], 'final_status': final_status}
            )

            results['success'] = True
            results['status'] = final_status
            results['duration_ms'] = elapsed_total_ms
            return results

        except Exception as unhandled_err:
            elapsed_total_ms = int((time.perf_counter() - overall_start) * 1000)
            logger.error(f"[US-40] Unhandled pipeline crash for video {video.id}: {unhandled_err}", exc_info=True)
            video.status = 'FAILED'
            video.save(update_fields=['status'])

            PipelineExecutionLog.objects.create(
                video=video,
                stage=PipelineExecutionLog.Stage.PIPELINE,
                status=PipelineExecutionLog.Status.FAILED,
                attempt=1,
                error_message=str(unhandled_err),
                execution_time_ms=elapsed_total_ms
            )

            results['success'] = False
            results['status'] = 'FAILED'
            results['error'] = str(unhandled_err)
            return results

    @classmethod
    def retry_pipeline(cls, video: PresentationVideo) -> Dict[str, Any]:
        """
        Manually triggers a full pipeline re-run for a previously failed or degraded video.
        Sets status to RETRYING during processing.
        """
        video.status = 'RETRYING'
        video.save(update_fields=['status'])

        PipelineExecutionLog.objects.create(
            video=video,
            stage=PipelineExecutionLog.Stage.PIPELINE,
            status=PipelineExecutionLog.Status.RETRY,
            attempt=1,
            details={'trigger': 'manual_user_retry'}
        )

        return cls.run_pipeline(video, force_refresh=True)

    @classmethod
    def get_pipeline_telemetry(cls, video: PresentationVideo) -> Dict[str, Any]:
        """
        Returns rich pipeline telemetry and log history for frontend resilience components.
        """
        logs = video.execution_logs.all()[:15]
        score = getattr(video, 'presentation_score', None)

        is_degraded = False
        if score and not score.has_behavioral_data:
            is_degraded = True
        elif video.status == 'PARTIALLY_COMPLETED':
            is_degraded = True

        log_data = []
        for log in logs:
            log_data.append({
                'id': log.id,
                'stage': log.stage,
                'status': log.status,
                'attempt': log.attempt,
                'error_message': log.error_message,
                'execution_time_ms': log.execution_time_ms,
                'created_at': log.created_at.isoformat(),
            })

        return {
            'video_id': video.id,
            'status': video.status,
            'is_degraded': is_degraded,
            'degradation_note': score.notes if (score and is_degraded) else '',
            'has_speech': hasattr(video, 'speech_analysis') and video.speech_analysis is not None,
            'has_behavioral': hasattr(video, 'behavioral_analysis') and video.behavioral_analysis is not None,
            'has_score': score is not None,
            'has_feedback': hasattr(video, 'ai_feedback') and video.ai_feedback is not None,
            'logs': log_data,
        }
