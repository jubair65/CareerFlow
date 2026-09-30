import logging
from typing import Optional, Dict, Any, Tuple
from apps.presentation.models import PresentationVideo, SpeechAnalysis, BehavioralAnalysis, PresentationScore

logger = logging.getLogger(__name__)


class PresentationScorer:
    """
    Presentation Scoring Engine (US-14)
    Synthesizes quantitative Speech Analysis (US-12) and Behavioral Analysis (US-13)
    metrics into a standardized 0-100 composite score with subcategory breakdowns.
    """

    # Weighting rubric constants
    WEIGHT_SPEECH = 0.50
    WEIGHT_BEHAVIORAL = 0.50

    # Speech sub-weights
    WEIGHT_PACE = 0.50
    WEIGHT_FILLER = 0.50

    # Behavioral sub-weights
    WEIGHT_EYE_CONTACT = 0.40
    WEIGHT_POSTURE = 0.30
    WEIGHT_ENGAGEMENT = 0.30

    # Benchmark targets
    OPTIMAL_WPM_MIN = 130
    OPTIMAL_WPM_MAX = 160
    FILLER_PENALTY_PER_OCCURRENCE = 5

    @classmethod
    def clamp_score(cls, value: float) -> int:
        """Clamp numeric score to closed interval [0, 100] as integer."""
        return max(0, min(100, int(round(value))))

    @classmethod
    def calculate_pace_score(cls, wpm: float) -> int:
        """
        Calculate pacing score based on 130-160 WPM ideal benchmark.
        1 pt deducted per WPM deviation outside ideal range.
        """
        if wpm <= 0:
            return 0
        if cls.OPTIMAL_WPM_MIN <= wpm <= cls.OPTIMAL_WPM_MAX:
            return 100
        elif wpm < cls.OPTIMAL_WPM_MIN:
            deduction = cls.OPTIMAL_WPM_MIN - wpm
            return cls.clamp_score(100 - deduction)
        else:
            deduction = wpm - cls.OPTIMAL_WPM_MAX
            return cls.clamp_score(100 - deduction)

    @classmethod
    def calculate_filler_score(cls, filler_count: int) -> int:
        """
        Calculate filler word control score.
        Deduct 5 points per filler occurrence from 100.
        """
        if filler_count <= 0:
            return 100
        deduction = filler_count * cls.FILLER_PENALTY_PER_OCCURRENCE
        return cls.clamp_score(100 - deduction)

    @classmethod
    def calculate_speech_score(cls, wpm: float, filler_count: int) -> Tuple[int, int, int]:
        """
        Calculates speech subscores:
        Returns: (pace_score, filler_score, composite_speech_score)
        """
        pace_score = cls.calculate_pace_score(wpm)
        filler_score = cls.calculate_filler_score(filler_count)
        composite = cls.clamp_score(
            (cls.WEIGHT_PACE * pace_score) + (cls.WEIGHT_FILLER * filler_score)
        )
        return pace_score, filler_score, composite

    @classmethod
    def calculate_behavioral_score(
        cls,
        eye_contact: int,
        posture: int,
        engagement: int
    ) -> Tuple[int, int, int, int]:
        """
        Calculates behavioral vision subscores:
        Returns: (eye_contact_score, posture_score, engagement_score, composite_behavioral_score)
        """
        eye = cls.clamp_score(eye_contact)
        post = cls.clamp_score(posture)
        eng = cls.clamp_score(engagement)
        composite = cls.clamp_score(
            (cls.WEIGHT_EYE_CONTACT * eye) +
            (cls.WEIGHT_POSTURE * post) +
            (cls.WEIGHT_ENGAGEMENT * eng)
        )
        return eye, post, eng, composite

    @classmethod
    def evaluate(
        cls,
        speech: Optional[SpeechAnalysis],
        behavioral: Optional[BehavioralAnalysis]
    ) -> Dict[str, Any]:
        """
        Evaluate composite presentation scores from speech and behavioral models.
        Handles graceful degradation if behavioral data is missing (US-40 alignment).
        """
        # Speech metrics evaluation
        if speech:
            pace_score, filler_score, speech_score = cls.calculate_speech_score(
                wpm=speech.words_per_minute,
                filler_count=speech.filler_word_count
            )
        else:
            pace_score, filler_score, speech_score = 0, 0, 0

        # Behavioral metrics evaluation with graceful degradation
        has_behavioral = behavioral is not None
        notes = []

        if has_behavioral:
            eye_score, posture_score, engagement_score, behavioral_score = cls.calculate_behavioral_score(
                eye_contact=behavioral.eye_contact_score,
                posture=behavioral.posture_score,
                engagement=behavioral.engagement_score
            )
            overall_score = cls.clamp_score(
                (cls.WEIGHT_SPEECH * speech_score) + (cls.WEIGHT_BEHAVIORAL * behavioral_score)
            )
        else:
            eye_score, posture_score, engagement_score, behavioral_score = 0, 0, 0, 0
            # Graceful degradation: Evaluate 100% on speech delivery
            overall_score = speech_score
            notes.append("Video quality was insufficient for facial tracking; score based on speech clarity.")

        return {
            'overall_score': overall_score,
            'speech_score': speech_score,
            'behavioral_score': behavioral_score,
            'pace_score': pace_score,
            'filler_score': filler_score,
            'eye_contact_score': eye_score,
            'posture_score': posture_score,
            'engagement_score': engagement_score,
            'has_behavioral_data': has_behavioral,
            'notes': " ".join(notes)
        }

    @classmethod
    def score_video(cls, video: PresentationVideo) -> PresentationScore:
        """
        Calculates or updates PresentationScore for the given PresentationVideo instance.
        """
        speech = getattr(video, 'speech_analysis', None)
        behavioral = getattr(video, 'behavioral_analysis', None)

        metrics = cls.evaluate(speech=speech, behavioral=behavioral)

        score_obj, _ = PresentationScore.objects.update_or_create(
            video=video,
            defaults=metrics
        )

        # Update video status to COMPLETED if active/ready
        if video.status not in ('FAILED', 'COMPLETED'):
            video.status = 'COMPLETED'
            video.save(update_fields=['status'])

        return score_obj


def calculate_presentation_score(video: PresentationVideo) -> PresentationScore:
    """Helper functional interface to calculate scores for a video."""
    return PresentationScorer.score_video(video)
