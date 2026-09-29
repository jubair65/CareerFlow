import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BaseTranscriptionService(ABC):
    """
    Abstract interface for speech-to-text transcription services.
    Enables seamless swapping between local models (faster-whisper, whisper)
    and external cloud APIs without altering downstream callers.
    """

    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file to text.

        Parameters:
            audio_path (str): Filesystem path to the WAV or MP3 audio file.

        Returns:
            dict with structure:
                {
                    "text": str,
                    "language": str,
                    "duration": float,
                    "segments": List[dict] # list of {"start": float, "end": float, "text": str}
                }
        """
        raise NotImplementedError


class FasterWhisperTranscriptionService(BaseTranscriptionService):
    """
    Local CTranslate2-accelerated Whisper transcription service (US-12-T3).
    Defaults to the 'base' model for optimal CPU speed and low memory footprint.
    """

    _cached_models: Dict[str, Any] = {}

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _get_model(self):
        """
        Lazily loads and caches the WhisperModel instance to prevent repeated model loading overhead.
        """
        cache_key = f"{self.model_size}_{self.device}_{self.compute_type}"
        if cache_key not in FasterWhisperTranscriptionService._cached_models:
            from faster_whisper import WhisperModel
            logger.info(
                f"Loading Faster-Whisper model '{self.model_size}' "
                f"on {self.device} with compute_type={self.compute_type}..."
            )
            FasterWhisperTranscriptionService._cached_models[cache_key] = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return FasterWhisperTranscriptionService._cached_models[cache_key]

    def transcribe(self, audio_path: str, beam_size: int = 5) -> Dict[str, Any]:
        """
        Transcribes the given audio file using faster-whisper.

        Returns:
            Dict containing transcript text, detected language, duration, and segments.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._get_model()

        segments_generator, info = model.transcribe(
            audio_path,
            beam_size=beam_size,
            vad_filter=True, # Voice Activity Detection filters out silent portions
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        segment_list = []
        transcript_parts = []

        for segment in segments_generator:
            text_cleaned = segment.text.strip()
            if text_cleaned:
                transcript_parts.append(text_cleaned)
                segment_list.append({
                    "id": segment.id,
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text_cleaned
                })

        full_transcript = " ".join(transcript_parts).strip()

        return {
            "text": full_transcript,
            "language": getattr(info, "language", "en"),
            "duration": round(getattr(info, "duration", 0.0), 2),
            "segments": segment_list
        }
