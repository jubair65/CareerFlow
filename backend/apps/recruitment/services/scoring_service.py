"""
Scoring Aggregation Service for Recruitment Rooms (US-23).
Combines candidate CV match scores (US-09) and video presentation scores (US-14)
using role-specific weighting (US-20) to compute a deterministic, fair,
and explainable Final Applicant Score.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, Tuple, Union
from django.utils import timezone
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.presentation.models import PresentationScore

logger = logging.getLogger(__name__)

DEFAULT_CV_WEIGHT = 50
DEFAULT_VIDEO_WEIGHT = 50


def round_score(val: float) -> float:
    """
    US-23-T1 & AC#6: Mathematically exact, deterministic rounding to 1 decimal place.
    Uses ROUND_HALF_UP and clamps values strictly within [0.0, 100.0].
    """
    d = Decimal(str(round(val, 4)))
    clamped = max(Decimal('0.0'), min(Decimal('100.0'), d))
    return float(clamped.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))



def resolve_room_weights(room: Optional[RecruitmentRoom]) -> Tuple[int, int]:
    """
    US-23-T1 & AC#2: Extracts and validates the configured weights for a room.
    Defaults to 50% CV / 50% Video if room has no configured weights or if
    the sum does not equal exactly 100%.
    """
    if not room:
        return DEFAULT_CV_WEIGHT, DEFAULT_VIDEO_WEIGHT

    cv_w = getattr(room, 'cv_weight', None)
    vid_w = getattr(room, 'video_weight', None)

    if cv_w is None or vid_w is None:
        logger.info(f"Room #{getattr(room, 'id', 'Unknown')} has unconfigured weights; using 50/50 default.")
        return DEFAULT_CV_WEIGHT, DEFAULT_VIDEO_WEIGHT

    try:
        cv_w_int = int(cv_w)
        vid_w_int = int(vid_w)
    except (ValueError, TypeError):
        return DEFAULT_CV_WEIGHT, DEFAULT_VIDEO_WEIGHT

    if cv_w_int < 0 or cv_w_int > 100 or vid_w_int < 0 or vid_w_int > 100:
        logger.warning(f"Room #{room.id} has invalid weight ranges ({cv_w_int}, {vid_w_int}); defaulting to 50/50.")
        return DEFAULT_CV_WEIGHT, DEFAULT_VIDEO_WEIGHT

    if cv_w_int + vid_w_int != 100:
        logger.warning(
            f"Room #{room.id} weights sum to {cv_w_int + vid_w_int} != 100; "
            f"falling back to default 50/50 split."
        )
        return DEFAULT_CV_WEIGHT, DEFAULT_VIDEO_WEIGHT

    return cv_w_int, vid_w_int


def extract_cv_match_score(application: CandidateApplication) -> Optional[float]:
    """
    US-23-T3: Integrates CV match score (US-09/US-10) for an application.
    Leverages matcher_bridge.get_applicant_cv_score_data to resolve or compute
    the match score against the room's job requirements.
    """
    if not application.cv:
        return None

    try:
        from apps.recruitment.services.matcher_bridge import get_applicant_cv_score_data
        data = get_applicant_cv_score_data(application.room, application)
        if data.get("has_score") and data.get("match_score") is not None:
            raw_score = float(data["match_score"])
            return min(100.0, max(0.0, round(raw_score, 1)))
    except Exception as e:
        logger.warning(f"Failed to extract CV match score for application #{application.id}: {e}")

    return None


def extract_video_presentation_score(application: CandidateApplication) -> Optional[float]:
    """
    US-23-T3: Integrates Video presentation score (US-14) for an application.
    Extracts overall_score from PresentationScore associated with application.video.
    """
    if not application.video:
        return None

    try:
        video = application.video
        # Check OneToOne relation presentation_score
        ps = getattr(video, 'presentation_score', None)
        if ps is None:
            # Query directly in case reverse relation cache is stale
            ps = PresentationScore.objects.filter(video=video).first()

        if ps is not None and ps.overall_score is not None:
            raw_score = float(ps.overall_score)
            return min(100.0, max(0.0, round(raw_score, 1)))
    except Exception as e:
        logger.warning(f"Failed to extract video presentation score for application #{application.id}: {e}")

    return None


def compute_weighted_score(
    cv_score: Optional[float],
    video_score: Optional[float],
    cv_weight: int,
    video_weight: int,
) -> Tuple[Optional[float], bool]:
    """
    US-23-T1 & US-23-T4: Core mathematical aggregation with graceful degradation.
    Returns:
        (final_score: Optional[float], is_partial_score: bool)

    Rules:
    - Both present: Final = (W_cv * S_cv + W_video * S_video) / 100, is_partial=False
    - CV only present (Video missing/incomplete): Proportional re-scaling -> Final = S_cv, is_partial=True
      (If W_cv == 0, Final = 0.0)
    - Video only present (CV missing/incomplete): Proportional re-scaling -> Final = S_video, is_partial=True
      (If W_video == 0, Final = 0.0)
    - Neither present: Final = None, is_partial=False
    """
    has_cv = cv_score is not None
    has_video = video_score is not None

    # Case A: Both CV and Video evaluated
    if has_cv and has_video:
        weighted_sum = (cv_weight * cv_score) + (video_weight * video_score)
        final_val = round_score(weighted_sum / 100.0)
        return final_val, False

    # Case B: Only CV evaluated
    if has_cv and not has_video:
        if cv_weight > 0:
            final_val = round_score(float(cv_score))
        else:
            final_val = 0.0
        return final_val, True

    # Case C: Only Video evaluated
    if not has_cv and has_video:
        if video_weight > 0:
            final_val = round_score(float(video_score))
        else:
            final_val = 0.0
        return final_val, True

    # Case D: Neither evaluated
    return None, False


def calculate_application_score(
    application_or_id: Union[int, CandidateApplication],
    persist: bool = True,
) -> Dict[str, Any]:
    """
    US-23-T2: Calculates and persists the final Applicant Score for a candidate application.
    """
    if isinstance(application_or_id, CandidateApplication):
        application = application_or_id
    else:
        application = CandidateApplication.objects.select_related(
            'room', 'cv', 'video'
        ).get(id=application_or_id)

    room = application.room
    cv_weight, video_weight = resolve_room_weights(room)

    cv_score = extract_cv_match_score(application)
    video_score = extract_video_presentation_score(application)

    final_score, is_partial_score = compute_weighted_score(
        cv_score=cv_score,
        video_score=video_score,
        cv_weight=cv_weight,
        video_weight=video_weight,
    )

    now = timezone.now()
    application.cv_score = cv_score
    application.video_score = video_score
    application.final_score = final_score
    application.is_partial_score = is_partial_score
    application.score_calculated_at = now

    if persist:
        application.save(
            update_fields=[
                'cv_score',
                'video_score',
                'final_score',
                'is_partial_score',
                'score_calculated_at',
            ]
        )

    return {
        "application_id": application.id,
        "room_id": room.id,
        "candidate_id": application.candidate_id,
        "cv_score": cv_score,
        "video_score": video_score,
        "final_score": final_score,
        "is_partial_score": is_partial_score,
        "weights_used": {
            "cv_weight": cv_weight,
            "video_weight": video_weight,
        },
        "score_calculated_at": now.isoformat(),
        "application": application,
    }


def calculate_room_applicant_scores(
    room_or_id: Union[int, RecruitmentRoom]
) -> Dict[str, Any]:
    """
    US-23-T5: Batch recalculates final applicant scores for all candidates in a recruitment room.
    Matches REST API contract for POST /api/recruitment/rooms/{room_id}/calculate-scores/
    """
    if isinstance(room_or_id, RecruitmentRoom):
        room = room_or_id
    else:
        room = RecruitmentRoom.objects.get(id=room_or_id)

    cv_weight, video_weight = resolve_room_weights(room)

    applications = CandidateApplication.objects.filter(room=room).select_related(
        'room', 'cv', 'video'
    )

    processed_count = 0
    updated_count = 0

    for app in applications:
        processed_count += 1
        res = calculate_application_score(app, persist=True)
        if res.get("final_score") is not None:
            updated_count += 1

    return {
        "message": "Scores successfully calculated for all room applicants",
        "room_id": room.id,
        "weights_used": {
            "cv_weight": cv_weight,
            "video_weight": video_weight,
        },
        "processed_count": processed_count,
        "updated_count": updated_count,
    }
