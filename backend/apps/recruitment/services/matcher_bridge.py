"""
CV Semantic Matcher Bridge for Recruitment Rooms (US-19-T5).
Bridges HR RecruitmentRoom role definitions and required skills to the
CV semantic matching engine (apps.cv.services.semantic_matcher).
"""

import logging
from typing import List, Dict, Any, Optional

from apps.recruitment.models import RecruitmentRoom
from apps.cv.models import CandidateCV, JobRequirement
from apps.cv.services.semantic_matcher import CVJobSemanticMatcher, MatchEvaluationResult

logger = logging.getLogger(__name__)


def extract_room_skills(room: RecruitmentRoom) -> List[str]:
    """
    Extracts a clean, unique list of skill strings from room.skills_required.
    Handles both list of strings ["Python", "React"] and structured dicts
    [{"name": "Python", "importance": "REQUIRED"}].
    """
    raw_skills = room.skills_required or []
    if not isinstance(raw_skills, list):
        return []

    unique_skills: List[str] = []
    seen = set()

    for item in raw_skills:
        skill_name = ""
        if isinstance(item, str):
            skill_name = item.strip()
        elif isinstance(item, dict) and 'name' in item:
            skill_name = str(item['name']).strip()

        if skill_name:
            lowered = skill_name.lower()
            if lowered not in seen:
                seen.add(lowered)
                unique_skills.append(skill_name)

    return unique_skills


def build_matcher_payload(room: RecruitmentRoom) -> Dict[str, Any]:
    """
    Formats recruitment room requirements into the payload expected by
    the CV semantic matching engine.
    """
    skills = extract_room_skills(room)
    description_parts = []
    if room.description:
        description_parts.append(room.description.strip())
    if room.requirements_text:
        description_parts.append(f"Requirements:\n{room.requirements_text.strip()}")

    combined_description = "\n\n".join(description_parts) or f"{room.title} opening at {room.company_name}"

    return {
        "room_id": room.id,
        "job_title": room.title,
        "company": room.company_name,
        "department": room.department or "",
        "role_category": room.role_category or "Engineering",
        "experience_level": room.experience_level,
        "job_description": combined_description,
        "required_skills": skills,
        "cv_weight": room.cv_weight,
        "video_weight": room.video_weight,
    }


def sync_room_to_job_requirement(room: RecruitmentRoom) -> JobRequirement:
    """
    Creates or synchronizes an underlying JobRequirement model instance
    so room requirements seamlessly integrate with existing CV matching
    dashboards and automated candidate filtering.
    """
    payload = build_matcher_payload(room)
    role_type = f"{payload['role_category']} • {room.get_experience_level_display()}"

    # Search for an existing JobRequirement linked to this title, company, and HR creator
    job_req = JobRequirement.objects.filter(
        title=room.title,
        company=room.company_name,
        created_by=room.created_by,
    ).first()

    if not job_req:
        job_req = JobRequirement.objects.create(
            title=room.title,
            company=room.company_name,
            role_type=role_type,
            description=payload['job_description'],
            required_skills=payload['required_skills'],
            threshold_score=70,
            created_by=room.created_by,
        )
        logger.info(f"Created JobRequirement #{job_req.id} for Room #{room.id} ({room.title})")
    else:
        job_req.role_type = role_type
        job_req.description = payload['job_description']
        job_req.required_skills = payload['required_skills']
        job_req.save()
        logger.info(f"Updated JobRequirement #{job_req.id} for Room #{room.id} ({room.title})")

    return job_req


def evaluate_candidate_for_room(
    room: RecruitmentRoom,
    cv: CandidateCV
) -> MatchEvaluationResult:
    """
    Directly evaluates a candidate's uploaded CV against the Room's
    configured role description, requirements text, and skill tags.
    """
    payload = build_matcher_payload(room)
    matcher = CVJobSemanticMatcher()

    return matcher.evaluate_match(
        cv=cv,
        job_title=payload['job_title'],
        job_description=payload['job_description'],
        required_skills=payload['required_skills'],
    )


def get_applicant_cv_score_data(
    room: RecruitmentRoom,
    application,
    request=None
) -> Dict[str, Any]:
    """
    US-10-T2 & US-10-T4: Extracts or computes the CV Match score and full skill breakdown
    for an applicant in a given recruitment room.
    Handles applicants without CV gracefully (US-10-T5).
    """
    from apps.cv.models import CVJobMatch
    from apps.cv.services.semantic_matcher import match_cv_to_job

    candidate = application.candidate
    candidate_name = getattr(candidate, 'full_name', '') or getattr(candidate, 'username', '')
    applied_at = application.applied_at
    status_str = application.status

    if not application.cv:
        return {
            "application_id": application.id,
            "candidate_id": candidate.id,
            "candidate_name": candidate_name,
            "candidate_email": candidate.email,
            "cv_id": None,
            "cv_filename": None,
            "cv_file_url": None,
            "has_cv": False,
            "has_score": False,
            "match_score": None,
            "keyword_coverage": 0,
            "category_scores": {},
            "skills_matched": [],
            "skills_missing": extract_room_skills(room),
            "strengths": [],
            "gaps": ["No CV document uploaded for this application."],
            "recommendations": ["Prompt candidate to submit an updated CV."],
            "applied_at": applied_at,
            "status": status_str,
        }

    cv = application.cv
    cv_url = None
    if request and cv.file:
        try:
            cv_url = request.build_absolute_uri(cv.file.url)
        except Exception:
            cv_url = cv.file.url if cv.file else None
    elif cv.file:
        try:
            cv_url = cv.file.url
        except Exception:
            cv_url = None

    # Check for existing CVJobMatch for this CV and room
    job_req = JobRequirement.objects.filter(
        title=room.title,
        company=room.company_name,
        created_by=room.created_by
    ).first()

    match_record = None
    if job_req:
        match_record = CVJobMatch.objects.filter(cv=cv, job=job_req).first()

    if not match_record:
        # Check by job_title
        match_record = CVJobMatch.objects.filter(cv=cv, job_title=room.title).first()

    if not match_record:
        # Compute on the fly and persist
        try:
            if not job_req:
                job_req = sync_room_to_job_requirement(room)
            match_record = match_cv_to_job(
                cv=cv,
                job_title=room.title,
                job_description=build_matcher_payload(room)['job_description'],
                required_skills=extract_room_skills(room),
                job_instance=job_req
            )
        except Exception as e:
            logger.warning(f"Error evaluating CV match for application #{application.id}: {e}")
            match_record = None

    if match_record:
        return {
            "application_id": application.id,
            "candidate_id": candidate.id,
            "candidate_name": candidate_name,
            "candidate_email": candidate.email,
            "cv_id": cv.id,
            "cv_filename": cv.original_filename,
            "cv_file_url": cv_url,
            "has_cv": True,
            "has_score": True,
            "match_score": match_record.match_score,
            "keyword_coverage": match_record.keyword_coverage,
            "category_scores": match_record.category_scores or {},
            "skills_matched": match_record.skills_matched or [],
            "skills_missing": match_record.skills_missing or [],
            "strengths": match_record.strengths or [],
            "gaps": match_record.gaps or [],
            "recommendations": match_record.recommendations or [],
            "applied_at": applied_at,
            "status": status_str,
        }

    return {
        "application_id": application.id,
        "candidate_id": candidate.id,
        "candidate_name": candidate_name,
        "candidate_email": candidate.email,
        "cv_id": cv.id,
        "cv_filename": cv.original_filename,
        "cv_file_url": cv_url,
        "has_cv": True,
        "has_score": False,
        "match_score": None,
        "keyword_coverage": 0,
        "category_scores": {},
        "skills_matched": [],
        "skills_missing": extract_room_skills(room),
        "strengths": [],
        "gaps": ["CV analysis in progress"],
        "recommendations": [],
        "applied_at": applied_at,
        "status": status_str,
    }


def get_room_applicants_cv_scores(
    room: RecruitmentRoom,
    search_query: Optional[str] = None,
    min_score: Optional[int] = None,
    request=None
) -> Dict[str, Any]:
    """
    US-10-T2: Retrieves all applicant CV scores for a room, performs filtering,
    and calculates statistical aggregates (average, highest, lowest).
    """
    from apps.recruitment.models import CandidateApplication

    applications = (
        CandidateApplication.objects.filter(room=room)
        .select_related('candidate', 'cv')
        .order_by('-applied_at')
    )

    results = []
    scores = []

    for app in applications:
        item = get_applicant_cv_score_data(room, app, request=request)

        # Apply search filter if provided
        if search_query:
            query = search_query.strip().lower()
            name_match = query in item['candidate_name'].lower()
            email_match = query in item['candidate_email'].lower()
            skill_match = any(query in sk.lower() for sk in item['skills_matched'])
            if not (name_match or email_match or skill_match):
                continue

        # Apply min_score filter if provided
        if min_score is not None:
            if item['match_score'] is None or item['match_score'] < min_score:
                continue

        results.append(item)
        if item['match_score'] is not None:
            scores.append(item['match_score'])

    total_applicants = len(results)
    scored_applicants = len(scores)
    average_cv_score = round(sum(scores) / scored_applicants, 1) if scored_applicants > 0 else None
    highest_cv_score = max(scores) if scored_applicants > 0 else None
    lowest_cv_score = min(scores) if scored_applicants > 0 else None

    return {
        "room_id": room.id,
        "room_title": room.title,
        "company_name": room.company_name,
        "department": room.department or "",
        "total_applicants": total_applicants,
        "scored_applicants": scored_applicants,
        "average_cv_score": average_cv_score,
        "highest_cv_score": highest_cv_score,
        "lowest_cv_score": lowest_cv_score,
        "results": results,
    }
