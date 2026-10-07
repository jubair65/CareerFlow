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
