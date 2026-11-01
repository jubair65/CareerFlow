"""
Applicant Ranking Service for Recruitment Rooms (US-24).
Provides deterministic ranking of candidates based on weighted final scores,
resolves ties using hierarchical criteria (CV score -> Video score -> Applied date),
and segregates unranked/incomplete applications.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from django.db.models import Q
from apps.recruitment.models import RecruitmentRoom, CandidateApplication

logger = logging.getLogger(__name__)


def get_score_tier(score: Optional[float]) -> str:
    """Classifies a score into a display tier for UI rendering."""
    if score is None:
        return "TIER_PENDING"
    if score >= 75.0:
        return "TIER_HIGH"
    if score >= 50.0:
        return "TIER_MEDIUM"
    return "TIER_LOW"


def get_rank_badge(rank: int) -> str:
    """Returns rank podium badge."""
    if rank == 1:
        return "GOLD"
    if rank == 2:
        return "SILVER"
    if rank == 3:
        return "BRONZE"
    return "STANDARD"


def determine_unranked_reason(application: CandidateApplication) -> str:
    """Explains why an application does not have a final score yet."""
    if not application.cv and not application.video:
        return "CV document and video presentation missing"
    if not application.cv:
        return "CV document missing"
    if not application.video:
        return "Video presentation missing"
    if application.status == CandidateApplication.Status.ANALYZING:
        return "AI analysis actively in progress"
    if application.status == CandidateApplication.Status.FAILED:
        return "Analysis processing failed"
    return "Pending score evaluation"


def get_ranked_room_applicants(
    room_or_id: Union[int, RecruitmentRoom],
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    ordering: str = "-final_score",
    include_unranked: bool = True,
    shortlisted_only: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    US-24-T2 & US-24-T5: Fetches, orders, and ranks candidates for a recruitment room.
    Applies multi-tier tie-breaking and segregates unranked applications.
    US-46: Supports shortlisted_only filtering.
    """
    if isinstance(room_or_id, RecruitmentRoom):
        room = room_or_id
    else:
        room = RecruitmentRoom.objects.get(id=room_or_id)

    # Base query for this room
    base_qs = CandidateApplication.objects.filter(room=room).select_related(
        'candidate', 'cv', 'video'
    )

    # Optional search filtering (candidate full name, email, or username)
    if search:
        search_term = search.strip()
        if search_term:
            base_qs = base_qs.filter(
                Q(candidate__full_name__icontains=search_term)
                | Q(candidate__email__icontains=search_term)
                | Q(candidate__username__icontains=search_term)
            )

    # Optional status filtering
    if status_filter:
        base_qs = base_qs.filter(status=status_filter)

    # Optional shortlisted only filtering (US-46 AC-3)
    if shortlisted_only:
        base_qs = base_qs.filter(is_shortlisted=True)

    total_count = base_qs.count()

    # Partition into ranked (final_score IS NOT NULL) and unranked (final_score IS NULL)
    ranked_qs = base_qs.filter(final_score__isnull=False)
    unranked_qs = base_qs.filter(final_score__isnull=True).order_by('applied_at', 'id')

    # Apply score range filters to ranked candidates
    if min_score is not None:
        ranked_qs = ranked_qs.filter(final_score__gte=min_score)
    if max_score is not None:
        ranked_qs = ranked_qs.filter(final_score__lte=max_score)

    # Build ordering clauses with deterministic tie-breaking
    # Primary tie-breaker: cv_score DESC -> video_score DESC -> applied_at ASC -> id ASC
    if ordering == 'final_score':
        order_clauses = ['final_score', 'cv_score', 'video_score', 'applied_at', 'id']
    elif ordering == '-cv_score':
        order_clauses = ['-cv_score', '-final_score', '-video_score', 'applied_at', 'id']
    elif ordering == 'cv_score':
        order_clauses = ['cv_score', 'final_score', 'video_score', 'applied_at', 'id']
    elif ordering == '-video_score':
        order_clauses = ['-video_score', '-final_score', '-cv_score', 'applied_at', 'id']
    elif ordering == 'video_score':
        order_clauses = ['video_score', 'final_score', 'cv_score', 'applied_at', 'id']
    elif ordering == 'applied_at':
        order_clauses = ['applied_at', '-final_score', 'id']
    elif ordering == '-applied_at':
        order_clauses = ['-applied_at', '-final_score', 'id']
    else:
        # Default: -final_score
        order_clauses = ['-final_score', '-cv_score', '-video_score', 'applied_at', 'id']

    ordered_ranked = ranked_qs.order_by(*order_clauses)

    ranked_results: List[Dict[str, Any]] = []
    for idx, app in enumerate(ordered_ranked):
        rank_num = idx + 1
        cand = app.candidate
        cand_name = getattr(cand, 'full_name', '') or getattr(cand, 'username', '')

        ranked_results.append({
            "rank": rank_num,
            "badge": get_rank_badge(rank_num),
            "application_id": app.id,
            "candidate_id": cand.id,
            "candidate_name": cand_name,
            "candidate_email": cand.email,
            "final_score": app.final_score,
            "score_tier": get_score_tier(app.final_score),
            "cv_score": app.cv_score,
            "video_score": app.video_score,
            "is_partial_score": app.is_partial_score,
            "score_calculated_at": app.score_calculated_at,
            "is_shortlisted": app.is_shortlisted,
            "shortlist_reason": app.shortlist_reason or '',
            "shortlisted_at": app.shortlisted_at,
            "status": app.status,
            "applied_at": app.applied_at,
        })

    unranked_results: List[Dict[str, Any]] = []
    if include_unranked:
        for app in unranked_qs:
            cand = app.candidate
            cand_name = getattr(cand, 'full_name', '') or getattr(cand, 'username', '')
            unranked_results.append({
                "application_id": app.id,
                "candidate_id": cand.id,
                "candidate_name": cand_name,
                "candidate_email": cand.email,
                "final_score": None,
                "score_tier": "TIER_PENDING",
                "cv_score": app.cv_score,
                "video_score": app.video_score,
                "is_partial_score": False,
                "is_shortlisted": app.is_shortlisted,
                "status": app.status,
                "applied_at": app.applied_at,
                "pending_reason": determine_unranked_reason(app),
            })

    return {
        "room_id": room.id,
        "room_title": room.title,
        "company_name": room.company_name,
        "department": room.department or "",
        "cv_weight": room.cv_weight,
        "video_weight": room.video_weight,
        "total_applicants": total_count,
        "ranked_count": len(ranked_results),
        "unranked_count": len(unranked_results),
        "results": ranked_results,
        "unranked": unranked_results,
    }
