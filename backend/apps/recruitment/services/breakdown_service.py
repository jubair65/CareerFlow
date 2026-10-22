"""
Applicant Score Breakdown & Explainability Service (US-27).
Provides granular mathematical transparency into composite Applicant Scores
combining CV semantic match scores and video presentation analysis metrics.
Enforces AC#1: CV and Video contributions, weights, and points are clearly displayed.
Enforces US-27-T5: Graceful degradation and clear explanation for missing components.
"""

import logging
from typing import Dict, Any, Optional
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied

from apps.recruitment.models import CandidateApplication, RecruitmentRoom
from apps.authentication.models import User
from apps.recruitment.services.scoring_service import (
    resolve_room_weights,
    round_score,
    compute_weighted_score,
    extract_cv_match_score,
    extract_video_presentation_score,
)
from apps.recruitment.services.matcher_bridge import get_applicant_cv_score_data

logger = logging.getLogger(__name__)


def get_applicant_score_breakdown(
    application: CandidateApplication,
    request_user: Optional[User] = None,
    request=None
) -> Dict[str, Any]:
    """
    US-27-T2, US-27-T4, US-27-T5: Compiles a complete explainable score breakdown
    for an applicant, detailing exact point contributions, weights applied,
    and missing data handling.
    """
    room = application.room

    # Authorization Check: Only room owner (HR Manager) can access score breakdown
    if request_user is not None:
        if room.created_by != request_user or request_user.role != User.Role.HR_MANAGER:
            raise DRFPermissionDenied(
                "Access forbidden: Only the HR Manager who owns this recruitment room can view applicant score breakdowns."
            )

    candidate = application.candidate
    candidate_name = getattr(candidate, 'full_name', '') or candidate.email.split('@')[0]

    cv_weight, video_weight = resolve_room_weights(room)

    # Resolve or extract component scores
    raw_cv_score = application.cv_score
    if raw_cv_score is None and application.cv:
        raw_cv_score = extract_cv_match_score(application)

    raw_video_score = application.video_score
    if raw_video_score is None and application.video:
        raw_video_score = extract_video_presentation_score(application)

    final_score = application.final_score
    is_partial_score = application.is_partial_score

    # If final_score wasn't precomputed, calculate dynamically
    if final_score is None and (raw_cv_score is not None or raw_video_score is not None):
        final_score, is_partial_score = compute_weighted_score(
            cv_score=raw_cv_score,
            video_score=raw_video_score,
            cv_weight=cv_weight,
            video_weight=video_weight,
        )

    # -------------------------------------------------------------------------
    # CV Component Contribution (US-27-T4)
    # -------------------------------------------------------------------------
    cv_available = raw_cv_score is not None
    cv_points_contributed: Optional[float] = None
    cv_percentage_of_total: Optional[float] = None
    cv_missing_reason: Optional[str] = None

    cv_submetrics: Dict[str, Any] = {
        "filename": application.cv.original_filename if application.cv else None,
        "skills_matched": [],
        "skills_missing": [],
        "match_score": raw_cv_score,
        "keyword_coverage": 0,
    }

    if cv_available:
        if not is_partial_score:
            # Full weighted points: (W_cv * S_cv) / 100
            cv_points_contributed = round_score((cv_weight * raw_cv_score) / 100.0)
            if final_score and final_score > 0:
                cv_percentage_of_total = round((cv_points_contributed / final_score) * 100.0, 1)
        else:
            # Partial: CV alone comprises 100% of the active score
            cv_points_contributed = round_score(raw_cv_score) if cv_weight > 0 else 0.0
            cv_percentage_of_total = 100.0 if cv_weight > 0 else 0.0

        # Attempt to populate granular skills details
        try:
            cv_data = get_applicant_cv_score_data(room, application, request=request)
            cv_submetrics["skills_matched"] = cv_data.get("skills_matched", [])
            cv_submetrics["skills_missing"] = cv_data.get("skills_missing", [])
            cv_submetrics["keyword_coverage"] = cv_data.get("keyword_coverage", 0)
        except Exception as e:
            logger.warning(f"Error fetching CV sub-metrics for application #{application.id}: {e}")
    else:
        if not application.cv:
            cv_missing_reason = "No CV file was uploaded for this application."
        else:
            cv_missing_reason = "CV text parsing or semantic match evaluation is currently pending."

    # -------------------------------------------------------------------------
    # Video Component Contribution (US-27-T4)
    # -------------------------------------------------------------------------
    video_available = raw_video_score is not None
    video_points_contributed: Optional[float] = None
    video_percentage_of_total: Optional[float] = None
    video_missing_reason: Optional[str] = None

    video_submetrics: Dict[str, Any] = {
        "speech_score": None,
        "visual_score": None,
        "grade_label": "N/A",
        "filler_words_count": 0,
        "wpm": 0,
        "summary": "",
    }

    if video_available:
        if not is_partial_score:
            # Full weighted points: (W_video * S_video) / 100
            video_points_contributed = round_score((video_weight * raw_video_score) / 100.0)
            if final_score and final_score > 0:
                video_percentage_of_total = round((video_points_contributed / final_score) * 100.0, 1)
        else:
            # Partial: Video alone comprises 100% of the active score
            video_points_contributed = round_score(raw_video_score) if video_weight > 0 else 0.0
            video_percentage_of_total = 100.0 if video_weight > 0 else 0.0

        # Attempt to populate granular video signals
        if application.video:
            try:
                score_obj = getattr(application.video, 'score', None)
                if score_obj:
                    video_submetrics["speech_score"] = getattr(score_obj, 'speech_score', None)
                    video_submetrics["visual_score"] = getattr(score_obj, 'visual_score', None)
                    video_submetrics["grade_label"] = getattr(score_obj, 'grade_label', "Competent")
                    video_submetrics["filler_words_count"] = getattr(score_obj, 'filler_words_count', 0)
                    video_submetrics["wpm"] = getattr(score_obj, 'words_per_minute', 0)

                feedback_obj = getattr(application.video, 'ai_feedback', None)
                if feedback_obj:
                    video_submetrics["summary"] = getattr(feedback_obj, 'summary', "")
            except Exception as e:
                logger.warning(f"Error fetching video sub-metrics for application #{application.id}: {e}")
    else:
        if not application.video:
            video_missing_reason = "No interview video was submitted for this application."
        else:
            video_missing_reason = "Video speech and behavioral metric pipelines are currently processing."

    # -------------------------------------------------------------------------
    # Formula & Missing Component Text (US-27-T1 & US-27-T5)
    # -------------------------------------------------------------------------
    if cv_available and video_available:
        formula_display = (
            f"({cv_weight}% × {raw_cv_score:.1f}) + ({video_weight}% × {raw_video_score:.1f}) = "
            f"{cv_points_contributed:.1f} + {video_points_contributed:.1f} = {final_score:.1f} / 100"
        )
        missing_components_explanation = None
    elif cv_available and not video_available:
        formula_display = f"100% × CV Match Score ({raw_cv_score:.1f}) = {final_score:.1f} / 100 (Pro-rated)"
        missing_components_explanation = (
            f"Video submission or analysis is missing ({video_missing_reason}). "
            f"To prevent penalizing the candidate unfairly, the Final Score was temporarily pro-rated "
            f"based solely on the CV Match Score."
        )
    elif not cv_available and video_available:
        formula_display = f"100% × Video Score ({raw_video_score:.1f}) = {final_score:.1f} / 100 (Pro-rated)"
        missing_components_explanation = (
            f"CV upload or parsing is missing ({cv_missing_reason}). "
            f"To prevent penalizing the candidate unfairly, the Final Score was temporarily pro-rated "
            f"based solely on the Video Presentation Score."
        )
    else:
        formula_display = "No evaluation data available yet."
        missing_components_explanation = (
            "Neither CV nor Video analysis is available. The score cannot be calculated until at least one component completes."
        )

    return {
        "application_id": application.id,
        "candidate_id": candidate.id,
        "candidate_name": candidate_name,
        "candidate_email": candidate.email,
        "room_id": room.id,
        "room_title": room.title,
        "final_score": final_score,
        "is_partial_score": is_partial_score,
        "score_calculated_at": application.score_calculated_at,
        "cv_weight": cv_weight,
        "video_weight": video_weight,
        "formula_display": formula_display,
        "missing_components_explanation": missing_components_explanation,
        "cv_component": {
            "name": "CV Semantic Match",
            "is_available": cv_available,
            "raw_score": raw_cv_score,
            "weight_percentage": cv_weight,
            "points_contributed": cv_points_contributed,
            "max_points_possible": float(cv_weight),
            "percentage_of_total": cv_percentage_of_total,
            "missing_reason": cv_missing_reason,
            "sub_metrics": cv_submetrics,
        },
        "video_component": {
            "name": "Video Presentation Analysis",
            "is_available": video_available,
            "raw_score": raw_video_score,
            "weight_percentage": video_weight,
            "points_contributed": video_points_contributed,
            "max_points_possible": float(video_weight),
            "percentage_of_total": video_percentage_of_total,
            "missing_reason": video_missing_reason,
            "sub_metrics": video_submetrics,
        },
    }
