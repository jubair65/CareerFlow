"""
HR Candidate Review & Human Decision Service (US-26).
Empowers HR Managers to review composite AI scores, candidate profile signals,
and record authoritative decisions (Confirm, Override, Reject, Hold) with audit logs.
Enforces AC#5: AI recommendations are strictly advisory and clearly labeled.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied as DRFPermissionDenied

from apps.recruitment.models import CandidateApplication, RecruitmentRoom
from apps.authentication.models import User
from apps.recruitment.services.matcher_bridge import get_applicant_cv_score_data

logger = logging.getLogger(__name__)

AI_ADVISORY_DISCLAIMER = (
    "AI-generated scores and shortlisting recommendations are advisory tools "
    "designed to support, not replace, human hiring decisions."
)


def get_candidate_review_data(application: CandidateApplication, request_user: User, request=None) -> Dict[str, Any]:
    """
    US-26-T2: Compiles all signals needed for the Candidate Review Modal:
    - Candidate info and application status
    - CV score and skill match breakdown
    - Video presentation score and behavioral metrics
    - AI shortlisting recommendation (clearly marked advisory)
    - HR review decision and audit trail
    """
    room = application.room

    # Authorization verification: only room owner can access review details
    if room.created_by != request_user:
        raise DRFPermissionDenied("You do not have permission to view applications for this recruitment room.")

    candidate = application.candidate
    candidate_name = getattr(candidate, 'full_name', '') or candidate.email.split('@')[0]

    # CV Summary & Skill Breakdown
    cv_summary: Dict[str, Any] = {
        "has_cv": bool(application.cv),
        "cv_filename": application.cv.original_filename if application.cv else None,
        "cv_score": application.cv_score,
        "skills_matched": [],
        "skills_missing": [],
        "match_score": None,
    }

    try:
        cv_data = get_applicant_cv_score_data(room, application, request=request)
        cv_summary["skills_matched"] = cv_data.get("skills_matched", [])
        cv_summary["skills_missing"] = cv_data.get("skills_missing", [])
        cv_summary["match_score"] = cv_data.get("match_score")
        cv_summary["keyword_coverage"] = cv_data.get("keyword_coverage", 0)
    except Exception as e:
        logger.warning(f"Error fetching CV breakdown for app {application.id}: {e}")

    # Video Presentation Summary & Behavioral Metrics
    video_summary: Dict[str, Any] = {
        "has_video": bool(application.video),
        "video_score": application.video_score,
        "grade_label": "N/A",
        "speech_score": None,
        "visual_score": None,
        "filler_words_count": 0,
        "wpm": 0,
        "summary": "",
        "strengths": [],
        "improvements": [],
    }

    if application.video:
        try:
            # Check video scores if relation exists
            video_score_obj = getattr(application.video, 'score', None)
            if video_score_obj:
                video_summary["speech_score"] = getattr(video_score_obj, 'speech_score', None)
                video_summary["visual_score"] = getattr(video_score_obj, 'visual_score', None)
                video_summary["grade_label"] = getattr(video_score_obj, 'grade_label', "Competent")
                video_summary["filler_words_count"] = getattr(video_score_obj, 'filler_words_count', 0)
                video_summary["wpm"] = getattr(video_score_obj, 'words_per_minute', 0)

            # Check AI feedback if relation exists
            feedback_obj = getattr(application.video, 'ai_feedback', None)
            if feedback_obj:
                video_summary["summary"] = getattr(feedback_obj, 'summary', "")
                video_summary["strengths"] = getattr(feedback_obj, 'strengths', [])
                video_summary["improvements"] = getattr(feedback_obj, 'improvements', [])
        except Exception as e:
            logger.warning(f"Error fetching Video feedback for app {application.id}: {e}")

    # Determine AI recommendation label (US-26 AC#5)
    if application.is_shortlisted:
        ai_recommendation = "RECOMMENDED_SHORTLIST"
        ai_recommendation_label = "AI Recommendation: Shortlist"
    else:
        ai_recommendation = "NOT_RECOMMENDED"
        ai_recommendation_label = "AI Recommendation: Not Shortlisted"

    decided_by_name = None
    decided_by_email = None
    if application.hr_decided_by:
        decided_by_name = getattr(application.hr_decided_by, 'full_name', '') or application.hr_decided_by.email
        decided_by_email = application.hr_decided_by.email

    return {
        "application_id": application.id,
        "room_id": room.id,
        "room_title": room.title,
        "candidate_id": candidate.id,
        "candidate_name": candidate_name,
        "candidate_email": candidate.email,
        "status": application.status,
        "applied_at": application.applied_at,

        # Scores
        "final_score": application.final_score,
        "cv_score": application.cv_score,
        "video_score": application.video_score,
        "cv_weight": room.cv_weight,
        "video_weight": room.video_weight,
        "is_partial_score": application.is_partial_score,
        "score_calculated_at": application.score_calculated_at,

        # AI Recommendation (Advisory)
        "is_shortlisted": application.is_shortlisted,
        "shortlist_reason": application.shortlist_reason,
        "shortlisted_at": application.shortlisted_at,
        "ai_recommendation": ai_recommendation,
        "ai_recommendation_label": ai_recommendation_label,
        "ai_disclaimer": AI_ADVISORY_DISCLAIMER,

        # Deep Signal Breakdowns
        "cv_summary": cv_summary,
        "video_summary": video_summary,

        # HR Decision Audit Trail (US-26 AC#4)
        "hr_decision": application.hr_decision,
        "hr_decision_display": application.get_hr_decision_display(),
        "hr_decision_notes": application.hr_decision_notes,
        "hr_decided_by_email": decided_by_email,
        "hr_decided_by_name": decided_by_name,
        "hr_decided_at": application.hr_decided_at,
    }


def record_candidate_review_decision(
    application: CandidateApplication,
    decision: str,
    notes: str,
    request_user: User
) -> Dict[str, Any]:
    """
    US-26-T3 & US-26-T5: Validates and persists an authoritative HR human review decision.
    - Enforces Room Owner authorization
    - Validates mandatory justification note when overriding AI recommendation
    - Persists audit fields: hr_decision, hr_decision_notes, hr_decided_by, hr_decided_at
    - Updates application shortlist flag according to human decision
    """
    room = application.room

    # Authorization Check (US-26-T5)
    if room.created_by != request_user or request_user.role != User.Role.HR_MANAGER:
        raise DRFPermissionDenied("Access forbidden: Only the HR Manager who owns this room can record hiring decisions.")

    clean_notes = (notes or "").strip()

    # Override validation (US-26 AC#3 & US-26-T6)
    if decision == CandidateApplication.HrDecision.OVERRIDDEN:
        if not clean_notes or len(clean_notes) < 5:
            raise ValidationError({
                "notes": "An explanatory note (minimum 5 characters) is required when overriding the AI recommendation."
            })

    # Update candidate shortlist status based on decision
    now = timezone.now()
    if decision == CandidateApplication.HrDecision.CONFIRMED:
        application.is_shortlisted = True
        application.shortlisted_at = now
        application.shortlist_reason = clean_notes or "Shortlist confirmed by HR review"
    elif decision == CandidateApplication.HrDecision.REJECTED:
        application.is_shortlisted = False
        application.shortlist_reason = f"Candidate rejected by HR review: {clean_notes}" if clean_notes else "Candidate rejected by HR review"
    elif decision == CandidateApplication.HrDecision.OVERRIDDEN:
        # Toggle or manually accept
        if application.is_shortlisted:
            application.is_shortlisted = False
            application.shortlist_reason = f"Shortlist recommendation manually overridden by HR: {clean_notes}"
        else:
            application.is_shortlisted = True
            application.shortlisted_at = now
            application.shortlist_reason = f"Candidate shortlisted via HR override: {clean_notes}"
    elif decision == CandidateApplication.HrDecision.ON_HOLD:
        # Keep current shortlist status but record hold
        application.shortlist_reason = f"Application placed on hold by HR: {clean_notes}" if clean_notes else "Application placed on hold by HR"

    # Save audit fields (US-26 AC#4 & US-26-T4)
    application.hr_decision = decision
    application.hr_decision_notes = clean_notes
    application.hr_decided_by = request_user
    application.hr_decided_at = now

    application.save(update_fields=[
        'is_shortlisted',
        'shortlisted_at',
        'shortlist_reason',
        'hr_decision',
        'hr_decision_notes',
        'hr_decided_by',
        'hr_decided_at',
    ])

    return {
        "application_id": application.id,
        "hr_decision": application.hr_decision,
        "hr_decision_display": application.get_hr_decision_display(),
        "hr_decision_notes": application.hr_decision_notes,
        "hr_decided_by": request_user.email,
        "hr_decided_at": application.hr_decided_at,
        "is_shortlisted": application.is_shortlisted,
        "message": f"HR review decision '{application.get_hr_decision_display()}' recorded successfully.",
    }
