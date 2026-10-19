"""
Automatic Candidate Shortlisting Service (US-25).
Evaluates room candidate applications against configurable shortlisting criteria:
- Minimum Score Threshold (MIN_SCORE)
- Required Candidate Count / Top N (TOP_N)
- Combined Criteria (COMBINED: Top N meeting Minimum Score)
- None / Disabled (NONE)

Guarantees deterministic ranking, tie-breaking, and transparent reason tracking.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from django.utils import timezone
from apps.recruitment.models import RecruitmentRoom, CandidateApplication

logger = logging.getLogger(__name__)


def validate_shortlisting_criteria(
    strategy: str,
    min_score: Optional[float] = None,
    top_n: Optional[int] = None,
) -> Tuple[bool, Dict[str, str]]:
    """
    US-25-T1 & AC#3: Validates shortlisting criteria with clear, human-readable error messages.
    Returns:
        (is_valid: bool, errors: dict)
    """
    errors: Dict[str, str] = {}
    valid_strategies = [choice[0] for choice in RecruitmentRoom.ShortlistStrategy.choices]

    if strategy not in valid_strategies:
        errors["shortlist_strategy"] = (
            f"Invalid strategy '{strategy}'. Must be one of: {', '.join(valid_strategies)}."
        )
        return False, errors

    if strategy in (RecruitmentRoom.ShortlistStrategy.MIN_SCORE, RecruitmentRoom.ShortlistStrategy.COMBINED):
        if min_score is None:
            errors["shortlist_min_score"] = "Minimum score threshold is required for this shortlisting strategy."
        else:
            try:
                ms = float(min_score)
                if ms < 0.0 or ms > 100.0:
                    errors["shortlist_min_score"] = "Minimum score threshold must be between 0.0 and 100.0."
            except (ValueError, TypeError):
                errors["shortlist_min_score"] = "Minimum score threshold must be a valid number."

    if strategy in (RecruitmentRoom.ShortlistStrategy.TOP_N, RecruitmentRoom.ShortlistStrategy.COMBINED):
        if top_n is None:
            errors["shortlist_top_n"] = "Required candidate count (Top N) is required for this shortlisting strategy."
        else:
            try:
                tn = int(top_n)
                if tn < 1:
                    errors["shortlist_top_n"] = "Required candidate count (Top N) must be at least 1."
                elif tn > 1000:
                    errors["shortlist_top_n"] = "Required candidate count (Top N) cannot exceed 1,000."
            except (ValueError, TypeError):
                errors["shortlist_top_n"] = "Required candidate count (Top N) must be a valid positive integer."

    return len(errors) == 0, errors


def evaluate_room_shortlist(
    room_or_id: Union[int, RecruitmentRoom],
    persist: bool = True,
) -> Dict[str, Any]:
    """
    US-25-T3 & US-25-T5: Evaluates automatic shortlisting rules for all applicants in a room.
    Persists shortlist status, explanation reason, and shortlisted_at timestamp.
    """
    if isinstance(room_or_id, RecruitmentRoom):
        room = room_or_id
    else:
        room = RecruitmentRoom.objects.get(id=room_or_id)

    strategy = room.shortlist_strategy
    min_score = room.shortlist_min_score
    top_n = room.shortlist_top_n

    applications = CandidateApplication.objects.filter(room=room).select_related(
        'candidate', 'cv', 'video'
    )

    now = timezone.now()

    # If shortlisting is disabled
    if strategy == RecruitmentRoom.ShortlistStrategy.NONE:
        updated_apps = []
        for app in applications:
            app.is_shortlisted = False
            app.shortlist_reason = "Automatic shortlisting is disabled for this room."
            app.shortlisted_at = None
            if persist:
                app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])
            updated_apps.append(app)

        return {
            "room_id": room.id,
            "room_title": room.title,
            "strategy": strategy,
            "min_score": min_score,
            "top_n": top_n,
            "total_applicants": len(updated_apps),
            "shortlisted_count": 0,
            "non_shortlisted_count": len(updated_apps),
            "shortlisted_applicants": [],
            "all_applicants": [
                {
                    "application_id": a.id,
                    "candidate_id": a.candidate_id,
                    "candidate_name": getattr(a.candidate, 'full_name', '') or a.candidate.username,
                    "candidate_email": a.candidate.email,
                    "final_score": a.final_score,
                    "is_shortlisted": False,
                    "shortlist_reason": a.shortlist_reason,
                    "shortlisted_at": None,
                }
                for a in updated_apps
            ]
        }

    # Partition applications into ranked (has final_score) and unranked (final_score is None)
    ranked_apps = []
    unranked_apps = []

    for app in applications:
        if app.final_score is not None:
            ranked_apps.append(app)
        else:
            unranked_apps.append(app)

    # Sort ranked applications using US-24 deterministic tie-breaking hierarchy:
    # 1. final_score DESC
    # 2. cv_score DESC
    # 3. video_score DESC
    # 4. applied_at ASC (earlier applicant preferred)
    # 5. id ASC
    def sort_key(app: CandidateApplication):
        cv = app.cv_score if app.cv_score is not None else -1.0
        vid = app.video_score if app.video_score is not None else -1.0
        applied_ts = app.applied_at.timestamp() if app.applied_at else 0.0
        return (-app.final_score, -cv, -vid, applied_ts, app.id)

    ranked_apps.sort(key=sort_key)

    # Process unranked candidates: Not shortlisted
    for app in unranked_apps:
        app.is_shortlisted = False
        app.shortlist_reason = "Pending final score evaluation (CV or video evaluation incomplete)."
        app.shortlisted_at = None
        if persist:
            app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])

    # Evaluate ranked candidates according to strategy
    shortlisted_results: List[Dict[str, Any]] = []
    all_evaluated: List[Dict[str, Any]] = []

    if strategy == RecruitmentRoom.ShortlistStrategy.MIN_SCORE:
        ms = float(min_score or 0.0)
        for idx, app in enumerate(ranked_apps):
            rank = idx + 1
            if app.final_score >= ms:
                app.is_shortlisted = True
                app.shortlist_reason = (
                    f"Met minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                )
                if not app.shortlisted_at:
                    app.shortlisted_at = now
            else:
                app.is_shortlisted = False
                app.shortlist_reason = (
                    f"Below minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                )
                app.shortlisted_at = None

            if persist:
                app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])

            app_dict = {
                "application_id": app.id,
                "candidate_id": app.candidate_id,
                "candidate_name": getattr(app.candidate, 'full_name', '') or app.candidate.username,
                "candidate_email": app.candidate.email,
                "rank": rank,
                "final_score": app.final_score,
                "cv_score": app.cv_score,
                "video_score": app.video_score,
                "is_shortlisted": app.is_shortlisted,
                "shortlist_reason": app.shortlist_reason,
                "shortlisted_at": app.shortlisted_at.isoformat() if app.shortlisted_at else None,
            }
            all_evaluated.append(app_dict)
            if app.is_shortlisted:
                shortlisted_results.append(app_dict)

    elif strategy == RecruitmentRoom.ShortlistStrategy.TOP_N:
        tn = int(top_n or 0)
        for idx, app in enumerate(ranked_apps):
            rank = idx + 1
            if rank <= tn:
                app.is_shortlisted = True
                app.shortlist_reason = (
                    f"Ranked #{rank} within required top {tn} candidates (Score: {app.final_score:.1f}%)."
                )
                if not app.shortlisted_at:
                    app.shortlisted_at = now
            else:
                app.is_shortlisted = False
                app.shortlist_reason = (
                    f"Ranked #{rank}, outside required top {tn} quota (Score: {app.final_score:.1f}%)."
                )
                app.shortlisted_at = None

            if persist:
                app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])

            app_dict = {
                "application_id": app.id,
                "candidate_id": app.candidate_id,
                "candidate_name": getattr(app.candidate, 'full_name', '') or app.candidate.username,
                "candidate_email": app.candidate.email,
                "rank": rank,
                "final_score": app.final_score,
                "cv_score": app.cv_score,
                "video_score": app.video_score,
                "is_shortlisted": app.is_shortlisted,
                "shortlist_reason": app.shortlist_reason,
                "shortlisted_at": app.shortlisted_at.isoformat() if app.shortlisted_at else None,
            }
            all_evaluated.append(app_dict)
            if app.is_shortlisted:
                shortlisted_results.append(app_dict)

    elif strategy == RecruitmentRoom.ShortlistStrategy.COMBINED:
        ms = float(min_score or 0.0)
        tn = int(top_n or 0)

        # Candidates who satisfy min_score threshold
        qualified_counter = 0

        for idx, app in enumerate(ranked_apps):
            rank = idx + 1
            meets_score = app.final_score >= ms

            if meets_score:
                qualified_counter += 1
                if qualified_counter <= tn:
                    app.is_shortlisted = True
                    app.shortlist_reason = (
                        f"Ranked #{rank} (#{qualified_counter} in qualified) meeting score {ms:.1f}% "
                        f"within top {tn} quota (Score: {app.final_score:.1f}%)."
                    )
                    if not app.shortlisted_at:
                        app.shortlisted_at = now
                else:
                    app.is_shortlisted = False
                    app.shortlist_reason = (
                        f"Met minimum score {ms:.1f}%, but exceeds top {tn} quota (Rank: #{rank}, Score: {app.final_score:.1f}%)."
                    )
                    app.shortlisted_at = None
            else:
                app.is_shortlisted = False
                app.shortlist_reason = (
                    f"Below minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                )
                app.shortlisted_at = None

            if persist:
                app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])

            app_dict = {
                "application_id": app.id,
                "candidate_id": app.candidate_id,
                "candidate_name": getattr(app.candidate, 'full_name', '') or app.candidate.username,
                "candidate_email": app.candidate.email,
                "rank": rank,
                "final_score": app.final_score,
                "cv_score": app.cv_score,
                "video_score": app.video_score,
                "is_shortlisted": app.is_shortlisted,
                "shortlist_reason": app.shortlist_reason,
                "shortlisted_at": app.shortlisted_at.isoformat() if app.shortlisted_at else None,
            }
            all_evaluated.append(app_dict)
            if app.is_shortlisted:
                shortlisted_results.append(app_dict)

    # Add unranked applications to all_evaluated
    for app in unranked_apps:
        all_evaluated.append({
            "application_id": app.id,
            "candidate_id": app.candidate_id,
            "candidate_name": getattr(app.candidate, 'full_name', '') or app.candidate.username,
            "candidate_email": app.candidate.email,
            "rank": None,
            "final_score": None,
            "cv_score": app.cv_score,
            "video_score": app.video_score,
            "is_shortlisted": False,
            "shortlist_reason": app.shortlist_reason,
            "shortlisted_at": None,
        })

    return {
        "room_id": room.id,
        "room_title": room.title,
        "strategy": strategy,
        "min_score": min_score,
        "top_n": top_n,
        "total_applicants": len(all_evaluated),
        "shortlisted_count": len(shortlisted_results),
        "non_shortlisted_count": len(all_evaluated) - len(shortlisted_results),
        "shortlisted_applicants": shortlisted_results,
        "all_applicants": all_evaluated,
    }
