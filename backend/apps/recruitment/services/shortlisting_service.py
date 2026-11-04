"""
Automatic Candidate Shortlisting Service (US-25 & US-26).
Evaluates room candidate applications against configurable shortlisting criteria:
- Minimum Score Threshold (MIN_SCORE)
- Required Candidate Count / Top N (TOP_N)
- Combined Criteria (COMBINED: Top N meeting Minimum Score)
- None / Disabled (NONE)

Authoritative Human HR Decisions (US-26: CONFIRMED, REJECTED, OVERRIDDEN) take
precedence over automated algorithmic recommendations.
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
    US-25 & US-26: Evaluates room shortlisting status for all applicants in a room.
    
    Precedence Hierarchy:
    1. Authoritative Human HR Decision (US-26: CONFIRMED, REJECTED, OVERRIDDEN, ON_HOLD)
       strictly overrides automated AI recommendation.
    2. Configurable Automated Rules (US-25: MIN_SCORE, TOP_N, COMBINED, NONE)
       apply deterministically for UNDECIDED applications.
    """
    if isinstance(room_or_id, RecruitmentRoom):
        room = room_or_id
    else:
        room = RecruitmentRoom.objects.get(id=room_or_id)

    strategy = room.shortlist_strategy
    min_score = room.shortlist_min_score
    top_n = room.shortlist_top_n

    applications = list(
        CandidateApplication.objects.filter(room=room).select_related(
            'candidate', 'cv', 'video'
        )
    )

    now = timezone.now()

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

    shortlisted_results: List[Dict[str, Any]] = []
    all_evaluated: List[Dict[str, Any]] = []

    # Combined strategy tracking counter for qualified candidates
    combined_qualified_counter = 0

    for idx, app in enumerate(ranked_apps):
        rank = idx + 1
        is_shortlisted = False
        shortlist_reason = ""
        shortlisted_at = None

        # 1. Authoritative Human HR Decision (US-26) takes highest precedence
        if app.hr_decision == CandidateApplication.HrDecision.CONFIRMED:
            is_shortlisted = True
            shortlist_reason = (
                app.hr_decision_notes.strip()
                if app.hr_decision_notes
                else (app.shortlist_reason or "Shortlist confirmed by HR review.")
            )
            shortlisted_at = app.hr_decided_at or app.shortlisted_at or now

        elif app.hr_decision == CandidateApplication.HrDecision.REJECTED:
            is_shortlisted = False
            notes = app.hr_decision_notes.strip() if app.hr_decision_notes else ""
            shortlist_reason = f"Candidate rejected by HR review: {notes}" if notes else "Candidate rejected by HR review."
            shortlisted_at = None

        elif app.hr_decision == CandidateApplication.HrDecision.OVERRIDDEN:
            notes = app.hr_decision_notes.strip() if app.hr_decision_notes else ""
            if app.is_shortlisted:
                is_shortlisted = True
                shortlist_reason = f"Candidate shortlisted via HR override: {notes}" if notes else "Candidate shortlisted via HR override."
                shortlisted_at = app.hr_decided_at or app.shortlisted_at or now
            else:
                is_shortlisted = False
                shortlist_reason = f"Shortlist recommendation overridden by HR: {notes}" if notes else "Shortlist recommendation overridden by HR."
                shortlisted_at = None

        elif app.hr_decision == CandidateApplication.HrDecision.ON_HOLD:
            is_shortlisted = False
            notes = app.hr_decision_notes.strip() if app.hr_decision_notes else ""
            shortlist_reason = f"Application placed on hold by HR: {notes}" if notes else "Application placed on hold by HR."
            shortlisted_at = None

        else:
            # 2. Automated rule evaluation for UNDECIDED candidates (US-25)
            if strategy == RecruitmentRoom.ShortlistStrategy.NONE:
                is_shortlisted = False
                shortlist_reason = "Automatic shortlisting is disabled for this room."
                shortlisted_at = None

            elif strategy == RecruitmentRoom.ShortlistStrategy.MIN_SCORE:
                ms = float(min_score or 0.0)
                if app.final_score >= ms:
                    is_shortlisted = True
                    shortlist_reason = f"Met minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                    shortlisted_at = app.shortlisted_at or now
                else:
                    is_shortlisted = False
                    shortlist_reason = f"Below minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                    shortlisted_at = None

            elif strategy == RecruitmentRoom.ShortlistStrategy.TOP_N:
                tn = int(top_n or 0)
                if rank <= tn:
                    is_shortlisted = True
                    shortlist_reason = f"Ranked #{rank} within required top {tn} candidates (Score: {app.final_score:.1f}%)."
                    shortlisted_at = app.shortlisted_at or now
                else:
                    is_shortlisted = False
                    shortlist_reason = f"Ranked #{rank}, outside required top {tn} quota (Score: {app.final_score:.1f}%)."
                    shortlisted_at = None

            elif strategy == RecruitmentRoom.ShortlistStrategy.COMBINED:
                ms = float(min_score or 0.0)
                tn = int(top_n or 0)
                if app.final_score >= ms:
                    combined_qualified_counter += 1
                    if combined_qualified_counter <= tn:
                        is_shortlisted = True
                        shortlist_reason = (
                            f"Ranked #{rank} (#{combined_qualified_counter} in qualified) meeting score {ms:.1f}% "
                            f"within top {tn} quota (Score: {app.final_score:.1f}%)."
                        )
                        shortlisted_at = app.shortlisted_at or now
                    else:
                        is_shortlisted = False
                        shortlist_reason = (
                            f"Met minimum score {ms:.1f}%, but exceeds top {tn} quota (Rank: #{rank}, Score: {app.final_score:.1f}%)."
                        )
                        shortlisted_at = None
                else:
                    is_shortlisted = False
                    shortlist_reason = f"Below minimum score threshold of {ms:.1f}% (Score: {app.final_score:.1f}%)."
                    shortlisted_at = None

            # Persist automated rule changes to DB if requested and undecided
            if persist:
                app.is_shortlisted = is_shortlisted
                app.shortlist_reason = shortlist_reason
                app.shortlisted_at = shortlisted_at
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
            "is_shortlisted": is_shortlisted,
            "shortlist_reason": shortlist_reason,
            "shortlisted_at": (
                shortlisted_at.isoformat()
                if hasattr(shortlisted_at, 'isoformat')
                else shortlisted_at
            ),
            "hr_decision": app.hr_decision,
            "hr_decision_display": app.get_hr_decision_display(),
            "hr_decision_notes": app.hr_decision_notes,
            "hr_decided_at": (
                app.hr_decided_at.isoformat() if app.hr_decided_at else None
            ),
        }
        all_evaluated.append(app_dict)
        if is_shortlisted:
            shortlisted_results.append(app_dict)

    # Process unranked applications (missing CV/video final score)
    for app in unranked_apps:
        is_shortlisted = False
        shortlist_reason = ""
        shortlisted_at = None

        # Even for unranked candidates, an explicit HR human decision is authoritative
        if app.hr_decision == CandidateApplication.HrDecision.CONFIRMED:
            is_shortlisted = True
            shortlist_reason = (
                app.hr_decision_notes.strip()
                if app.hr_decision_notes
                else (app.shortlist_reason or "Shortlist confirmed by HR review.")
            )
            shortlisted_at = app.hr_decided_at or app.shortlisted_at or now

        elif app.hr_decision == CandidateApplication.HrDecision.REJECTED:
            is_shortlisted = False
            notes = app.hr_decision_notes.strip() if app.hr_decision_notes else ""
            shortlist_reason = f"Candidate rejected by HR review: {notes}" if notes else "Candidate rejected by HR review."
            shortlisted_at = None

        elif app.hr_decision == CandidateApplication.HrDecision.OVERRIDDEN:
            notes = app.hr_decision_notes.strip() if app.hr_decision_notes else ""
            if app.is_shortlisted:
                is_shortlisted = True
                shortlist_reason = f"Candidate shortlisted via HR override: {notes}" if notes else "Candidate shortlisted via HR override."
                shortlisted_at = app.hr_decided_at or app.shortlisted_at or now
            else:
                is_shortlisted = False
                shortlist_reason = f"Shortlist recommendation overridden by HR: {notes}" if notes else "Shortlist recommendation overridden by HR."
                shortlisted_at = None

        else:
            is_shortlisted = False
            shortlist_reason = "Pending final score evaluation (CV or video evaluation incomplete)."
            shortlisted_at = None
            if persist:
                app.is_shortlisted = False
                app.shortlist_reason = shortlist_reason
                app.shortlisted_at = None
                app.save(update_fields=['is_shortlisted', 'shortlist_reason', 'shortlisted_at'])

        app_dict = {
            "application_id": app.id,
            "candidate_id": app.candidate_id,
            "candidate_name": getattr(app.candidate, 'full_name', '') or app.candidate.username,
            "candidate_email": app.candidate.email,
            "rank": None,
            "final_score": None,
            "cv_score": app.cv_score,
            "video_score": app.video_score,
            "is_shortlisted": is_shortlisted,
            "shortlist_reason": shortlist_reason,
            "shortlisted_at": (
                shortlisted_at.isoformat()
                if hasattr(shortlisted_at, 'isoformat')
                else shortlisted_at
            ),
            "hr_decision": app.hr_decision,
            "hr_decision_display": app.get_hr_decision_display(),
            "hr_decision_notes": app.hr_decision_notes,
            "hr_decided_at": (
                app.hr_decided_at.isoformat() if app.hr_decided_at else None
            ),
        }
        all_evaluated.append(app_dict)
        if is_shortlisted:
            shortlisted_results.append(app_dict)

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
