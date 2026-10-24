"""
Applicant Comparison Service for Recruitment Rooms (US-28).
Provides side-by-side comparison of 2 to 4 candidates in a recruitment room,
extracting CV match scores, video presentation signals, speech metrics,
and calculating best-in-category differentials and variance indicators.
"""

import logging
from typing import Dict, Any, List, Optional
from rest_framework.exceptions import ValidationError, PermissionDenied as DRFPermissionDenied

from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.authentication.models import User
from apps.recruitment.services.scoring_service import (
    resolve_room_weights,
    compute_weighted_score,
)
from apps.recruitment.services.matcher_bridge import get_applicant_cv_score_data
from apps.presentation.models import PresentationScore, SpeechAnalysis, BehavioralAnalysis

logger = logging.getLogger(__name__)


def get_candidate_avatar_initials(name: str) -> str:
    """Generates two-letter uppercase initials from full name or email prefix."""
    if not name:
        return "CA"
    parts = [p.strip() for p in name.split() if p.strip()]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    elif len(parts) == 1:
        return parts[0][0].upper()
    return "CA"


def get_score_tier(score: Optional[float]) -> str:
    """Classifies a score into standard display tiers."""
    if score is None:
        return "TIER_PENDING"
    if score >= 75.0:
        return "TIER_HIGH"
    if score >= 50.0:
        return "TIER_MEDIUM"
    return "TIER_LOW"


def compare_room_applicants(
    room: RecruitmentRoom,
    application_ids: List[int],
    request_user: Optional[User] = None,
    request=None
) -> Dict[str, Any]:
    """
    US-28-T2 & US-28-T5: Compiles a unified side-by-side comparison matrix for 2 to 4 applicants.
    Validates room ownership, enforces applicant limits, handles missing scores gracefully,
    and identifies best-in-category performance differentials.
    """
    # 1. Multi-Tenant Authorization Check (AC#6)
    if request_user is not None:
        if room.created_by != request_user or request_user.role != User.Role.HR_MANAGER:
            raise DRFPermissionDenied(
                "Access forbidden: Only the HR Manager who owns this recruitment room can compare applicants."
            )

    # 2. Enforce 2 to 4 applicants limit (AC#5)
    unique_ids = list(dict.fromkeys(application_ids))
    if len(unique_ids) < 2:
        raise ValidationError("At least 2 applicants are required for side-by-side comparison.")
    if len(unique_ids) > 4:
        raise ValidationError("Maximum 4 applicants can be compared simultaneously.")

    # 3. Fetch applications and verify all belong to this room
    apps_qs = CandidateApplication.objects.filter(
        room=room,
        id__in=unique_ids
    ).select_related('candidate', 'cv', 'video', 'hr_decided_by')

    apps_dict = {app.id: app for app in apps_qs}
    missing_ids = [aid for aid in unique_ids if aid not in apps_dict]
    if missing_ids:
        raise ValidationError(
            f"Application(s) with ID(s) {missing_ids} do not belong to this recruitment room."
        )

    # Maintain requested order
    ordered_apps = [apps_dict[aid] for aid in unique_ids]

    cv_weight, video_weight = resolve_room_weights(room)

    # 4. Extract metrics for each candidate
    raw_candidates: List[Dict[str, Any]] = []
    final_scores_for_avg: List[float] = []

    for app in ordered_apps:
        cand = app.candidate
        cand_name = getattr(cand, 'full_name', '') or cand.email.split('@')[0]
        initials = get_candidate_avatar_initials(cand_name)

        # Final Score resolution
        final_score = app.final_score
        is_partial = app.is_partial_score
        cv_score = app.cv_score
        video_score = app.video_score

        if final_score is None and (cv_score is not None or video_score is not None):
            final_score, is_partial = compute_weighted_score(
                cv_score=cv_score,
                video_score=video_score,
                cv_weight=cv_weight,
                video_weight=video_weight
            )

        if final_score is not None:
            final_scores_for_avg.append(final_score)

        # CV details (matched skills, missing skills, keyword coverage)
        matched_skills: List[str] = []
        missing_skills: List[str] = []
        keyword_coverage = 0.0

        if app.cv:
            try:
                cv_data = get_applicant_cv_score_data(room, app, request=request)
                matched_skills = [
                    s.get('name', str(s)) if isinstance(s, dict) else str(s)
                    for s in cv_data.get('skills_matched', [])
                ]
                missing_skills = [
                    s.get('name', str(s)) if isinstance(s, dict) else str(s)
                    for s in cv_data.get('skills_missing', [])
                ]
                keyword_coverage = float(cv_data.get('keyword_coverage', 0) or 0)
            except Exception as e:
                logger.warning(f"Error fetching CV comparison signals for app #{app.id}: {e}")

        # Video presentation details
        wpm = 0.0
        filler_words_count = 0
        eye_contact_percent: Optional[float] = None
        posture_score: Optional[float] = None
        speech_score: Optional[float] = None
        visual_score: Optional[float] = None

        if app.video:
            video = app.video
            try:
                # 1. Check PresentationScore
                ps = getattr(video, 'presentation_score', None)
                if ps is None:
                    ps = PresentationScore.objects.filter(video=video).first()

                if ps:
                    if ps.speech_score is not None:
                        speech_score = float(ps.speech_score)
                    if ps.behavioral_score is not None:
                        visual_score = float(ps.behavioral_score)
                    if ps.eye_contact_score is not None:
                        eye_contact_percent = float(ps.eye_contact_score)
                    if ps.posture_score is not None:
                        posture_score = float(ps.posture_score)

                # 2. Check SpeechAnalysis
                sa = getattr(video, 'speech_analysis', None)
                if sa is None:
                    sa = SpeechAnalysis.objects.filter(video=video).first()
                if sa:
                    wpm = float(sa.words_per_minute)
                    filler_words_count = sa.filler_word_count

                # 3. Check BehavioralAnalysis if eye_contact/posture still None
                if eye_contact_percent is None or posture_score is None:
                    ba = getattr(video, 'behavioral_analysis', None)
                    if ba is None:
                        ba = BehavioralAnalysis.objects.filter(video=video).first()
                    if ba:
                        if eye_contact_percent is None and ba.eye_contact_score is not None:
                            eye_contact_percent = float(ba.eye_contact_score)
                        if posture_score is None and ba.posture_score is not None:
                            posture_score = float(ba.posture_score)
            except Exception as e:
                logger.warning(f"Error fetching video comparison signals for app #{app.id}: {e}")

        raw_candidates.append({
            "application_id": app.id,
            "candidate_id": cand.id,
            "candidate_name": cand_name,
            "email": cand.email,
            "avatar_initials": initials,
            "final_score": final_score,
            "score_tier": get_score_tier(final_score),
            "is_partial_score": is_partial,
            "cv_score": cv_score,
            "video_score": video_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "keyword_coverage": round(keyword_coverage, 1),
            "wpm": round(wpm, 1),
            "eye_contact_percent": round(eye_contact_percent, 1) if eye_contact_percent is not None else None,
            "posture_score": round(posture_score, 1) if posture_score is not None else None,
            "filler_words_count": filler_words_count,
            "speech_score": round(speech_score, 1) if speech_score is not None else None,
            "visual_score": round(visual_score, 1) if visual_score is not None else None,
            "is_shortlisted": app.is_shortlisted,
            "shortlist_reason": app.shortlist_reason or "",
            "hr_decision": app.hr_decision or "PENDING",
            "hr_decision_display": app.get_hr_decision_display() if hasattr(app, 'get_hr_decision_display') else (app.hr_decision or "Pending Review"),
            "applied_at": app.applied_at,
            "best_in": [],
        })

    # 5. Compute best-in-category highlights across the comparison group (US-28-T5 & AC#4)
    valid_final_scores = [c["final_score"] for c in raw_candidates if c["final_score"] is not None]
    max_final = max(valid_final_scores) if valid_final_scores else None

    valid_cv_scores = [c["cv_score"] for c in raw_candidates if c["cv_score"] is not None]
    max_cv = max(valid_cv_scores) if valid_cv_scores else None

    valid_video_scores = [c["video_score"] for c in raw_candidates if c["video_score"] is not None]
    max_video = max(valid_video_scores) if valid_video_scores else None

    valid_eye_scores = [c["eye_contact_percent"] for c in raw_candidates if c["eye_contact_percent"] is not None]
    max_eye = max(valid_eye_scores) if valid_eye_scores else None

    valid_skill_counts = [len(c["matched_skills"]) for c in raw_candidates if c["matched_skills"]]
    max_skills_count = max(valid_skill_counts) if valid_skill_counts and max(valid_skill_counts) > 0 else None

    for c in raw_candidates:
        best_flags: List[str] = []
        if max_final is not None and c["final_score"] is not None and c["final_score"] == max_final:
            best_flags.append("final_score")
        if max_cv is not None and c["cv_score"] is not None and c["cv_score"] == max_cv:
            best_flags.append("cv_score")
        if max_video is not None and c["video_score"] is not None and c["video_score"] == max_video:
            best_flags.append("video_score")
        if max_eye is not None and c["eye_contact_percent"] is not None and c["eye_contact_percent"] == max_eye:
            best_flags.append("eye_contact")
        if max_skills_count is not None and len(c["matched_skills"]) == max_skills_count:
            best_flags.append("skills_match")
        c["best_in"] = best_flags

    # Summary Statistics
    avg_score = round(sum(final_scores_for_avg) / len(final_scores_for_avg), 1) if final_scores_for_avg else None

    return {
        "room_id": room.id,
        "room_title": room.title,
        "company_name": room.company_name,
        "cv_weight": cv_weight,
        "video_weight": video_weight,
        "comparison_count": len(raw_candidates),
        "highest_final_score": max_final,
        "average_final_score": avg_score,
        "applicants": raw_candidates,
    }
