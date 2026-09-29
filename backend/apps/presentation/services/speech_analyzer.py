import os
import logging
from typing import Optional
from django.db import transaction

from apps.presentation.models import PresentationVideo, SpeechAnalysis
from apps.presentation.services.audio_extractor import extract_audio, cleanup_audio_file
from apps.presentation.services.transcription_service import (
    BaseTranscriptionService,
    FasterWhisperTranscriptionService,
)
from apps.presentation.services.speech_metrics import (
    count_words,
    calculate_wpm,
    detect_filler_words,
    calculate_clarity_score,
)

logger = logging.getLogger(__name__)


class SpeechAnalyzer:
    """
    Orchestration service for US-12 Speech Analysis pipeline.
    Combines audio extraction, Whisper transcription, WPM calculation,
    filler word taxonomy detection, and database persistence.
    """

    def __init__(self, transcription_service: Optional[BaseTranscriptionService] = None):
        self.transcription_service = transcription_service or FasterWhisperTranscriptionService()

    def analyze_presentation_video(self, video: PresentationVideo) -> SpeechAnalysis:
        """
        Executes complete speech analysis workflow for a candidate's PresentationVideo.

        Steps:
            1. Update video status to PROCESSING_SPEECH
            2. Extract 16kHz mono WAV audio
            3. Transcribe audio to text
            4. Compute speech metrics (WPM, filler count/breakdown, clarity score)
            5. Store results in SpeechAnalysis database table (US-12-T6)
            6. Cleanup staging audio file
        """
        if not video.file:
            raise ValueError(f"PresentationVideo ID {video.id} has no associated video file.")

        # Safely resolve path whether absolute (e.g. tests) or relative to MEDIA_ROOT
        if hasattr(video.file, 'name') and os.path.isabs(video.file.name) and os.path.exists(video.file.name):
            video_path = video.file.name
        else:
            try:
                video_path = video.file.path
            except Exception:
                from django.conf import settings
                video_path = os.path.join(settings.MEDIA_ROOT, str(video.file))

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file does not exist at {video_path}")

        # Step 1: Update status
        video.status = 'PROCESSING_SPEECH'
        video.save(update_fields=['status'])

        temp_audio_path = None
        try:
            # Step 2: Extract audio
            temp_audio_path = extract_audio(video_path)

            # Step 3: Transcribe
            transcription_result = self.transcription_service.transcribe(temp_audio_path)
            transcript = transcription_result.get("text", "")
            duration = transcription_result.get("duration", 0.0)

            # Fallback to video duration if Whisper duration is 0
            if duration <= 0 and video.duration_seconds > 0:
                duration = float(video.duration_seconds)

            # Step 4: Compute metrics
            total_words = count_words(transcript)
            wpm = calculate_wpm(total_words, duration)
            filler_data = detect_filler_words(transcript)
            filler_count = filler_data["filler_word_count"]
            filler_breakdown = filler_data["filler_words_breakdown"]

            clarity = calculate_clarity_score(
                wpm=wpm,
                filler_count=filler_count,
                total_words=total_words,
                duration_seconds=duration,
            )

            # Step 5: Persist in database
            with transaction.atomic():
                speech_record, _ = SpeechAnalysis.objects.update_or_create(
                    video=video,
                    defaults={
                        "transcript": transcript,
                        "words_per_minute": wpm,
                        "filler_word_count": filler_count,
                        "filler_words_breakdown": filler_breakdown,
                        "clarity_score": clarity,
                        "duration_seconds": duration,
                    }
                )
                video.status = 'READY_FOR_ANALYSIS'
                video.save(update_fields=['status'])

            logger.info(
                f"Successfully completed speech analysis for video {video.id}: "
                f"{total_words} words, {wpm} WPM, {filler_count} fillers, clarity {clarity}"
            )
            return speech_record

        except Exception as e:
            logger.error(f"Speech analysis failed for video {video.id}: {e}")
            video.status = 'FAILED'
            video.save(update_fields=['status'])
            raise e
        finally:
            if temp_audio_path:
                cleanup_audio_file(temp_audio_path)


def analyze_speech(video: PresentationVideo) -> SpeechAnalysis:
    """
    Functional helper to trigger speech analysis on a presentation video.
    """
    analyzer = SpeechAnalyzer()
    return analyzer.analyze_presentation_video(video)
