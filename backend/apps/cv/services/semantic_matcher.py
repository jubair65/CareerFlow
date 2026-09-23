"""
CV-Job Semantic Matching Engine (US-09).
Calculates semantic similarity (0-100), keyword coverage, sub-signal category breakdown,
and skill gap analysis between a parsed candidate CV and job requirements/descriptions.
"""

import re
import math
import logging
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

from apps.cv.models import CandidateCV, ParsedCV, JobRequirement, CVJobMatch
from apps.cv.services.pipeline import default_pipeline
from apps.cv.services.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)


# Contextual keywords for category sub-signals (matching design in CareerFlow-Recruitment-Coach)
CATEGORY_KEYWORDS = {
    'domain_craft': [
        'design', 'architecture', 'engineering', 'development', 'system', 'build',
        'software', 'product', 'code', 'quality', 'technical', 'scale', 'craft',
        'implementation', 'frontend', 'backend', 'fullstack', 'database', 'cloud'
    ],
    'collaboration': [
        'collaboration', 'collaborated', 'team', 'cross-functional', 'stakeholder',
        'partnered', 'communicated', 'agile', 'scrum', 'mentored', 'alignment',
        'workshops', 'review', 'feedback', 'user-centered'
    ],
    'leadership': [
        'led', 'lead', 'managed', 'spearheaded', 'pioneered', 'directed', 'championed',
        'ownership', 'strategy', 'roadmap', 'decision', 'drive', 'initiated',
        'architected', 'governance'
    ],
    'accessibility': [
        'accessibility', 'a11y', 'wcag', 'inclusive', 'usability', 'compliance',
        'standards', 'performance', 'testing', 'security', 'audit', 'best practices'
    ],
}


@dataclass
class MatchEvaluationResult:
    match_score: int
    keyword_coverage: int
    category_scores: Dict[str, int]
    skills_matched: List[str]
    skills_missing: List[str]
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]


class CVJobSemanticMatcher:
    """
    NLP & Skill Taxonomies Semantic Matching Engine.
    Evaluates candidate CV against job requirement brief or text.
    """

    def __init__(self):
        self.skill_extractor = SkillExtractor()

    def tokenize_text(self, text: str) -> List[str]:
        """Convert text into cleaned words/tokens."""
        clean = re.sub(r'[^a-zA-Z0-9\s#\+\-\.]', ' ', text.lower())
        tokens = [w for w in clean.split() if len(w) >= 2]
        return tokens

    def compute_tfidf_cosine_similarity(self, cv_text: str, job_text: str) -> float:
        """
        Calculate cosine similarity between CV raw text and Job text using word frequencies.
        """
        tokens_cv = self.tokenize_text(cv_text)
        tokens_job = self.tokenize_text(job_text)

        if not tokens_cv or not tokens_job:
            return 0.5  # Neutral default

        counts_cv = Counter(tokens_cv)
        counts_job = Counter(tokens_job)

        all_words: Set[str] = set(counts_cv.keys()).union(set(counts_job.keys()))
        if not all_words:
            return 0.5

        dot_product = sum(counts_cv[w] * counts_job[w] for w in all_words)
        magnitude_cv = math.sqrt(sum(v ** 2 for v in counts_cv.values()))
        magnitude_job = math.sqrt(sum(v ** 2 for v in counts_job.values()))

        if magnitude_cv == 0 or magnitude_job == 0:
            return 0.5

        return dot_product / (magnitude_cv * magnitude_job)

    def evaluate_category_score(self, text: str, category_key: str) -> int:
        """
        Evaluate score (0-100) for sub-signal categories based on keyword occurrences.
        """
        keywords = CATEGORY_KEYWORDS.get(category_key, [])
        if not keywords:
            return 75

        lowered = text.lower()
        matches = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', lowered))

        # Base threshold matching
        if matches >= 5:
            return min(100, 85 + (matches - 5) * 3)
        elif matches >= 3:
            return 78 + (matches - 3) * 3
        elif matches >= 1:
            return 65 + (matches - 1) * 6
        return 50

    def evaluate_match(
        self,
        cv: CandidateCV,
        job_title: str,
        job_description: str,
        required_skills: Optional[List[str]] = None
    ) -> MatchEvaluationResult:
        """
        Perform complete semantic matching calculation between a candidate CV and job requirements.
        """
        # Ensure CV text and parsed skills exist
        parsed_data = getattr(cv, 'parsed_data', None)
        if not parsed_data:
            try:
                parsed_data = ParsedCV.objects.filter(cv=cv).first()
            except Exception:
                parsed_data = None

        if not parsed_data:
            # Auto-run extraction pipeline if not yet parsed
            result = default_pipeline.process_candidate_cv(cv)
            parsed_data, _ = ParsedCV.objects.update_or_create(
                cv=cv,
                defaults={
                    'raw_text': result.raw_text,
                    'skills': result.skills,
                    'education': result.education,
                    'experience': result.experience,
                }
            )

        cv_text = parsed_data.raw_text or ""
        cv_skills = [s.strip().lower() for s in (parsed_data.skills or [])]

        # Extract skills from job description if required_skills list is empty or minimal
        explicit_skills = [s.strip() for s in (required_skills or []) if s.strip()]
        extracted_job_skills = self.skill_extractor.extract_skills(f"{job_title}\n{job_description}")

        all_job_skills_dict: Dict[str, str] = {}
        for s in explicit_skills + extracted_job_skills:
            all_job_skills_dict[s.lower()] = s

        # Identify matched vs missing skills
        matched_skills: List[str] = []
        missing_skills: List[str] = []

        cv_text_lowered = cv_text.lower()
        for lower_skill, orig_skill in all_job_skills_dict.items():
            if lower_skill in cv_skills or re.search(r'\b' + re.escape(lower_skill) + r'\b', cv_text_lowered):
                matched_skills.append(orig_skill)
            else:
                missing_skills.append(orig_skill)

        total_job_skills = len(all_job_skills_dict)
        if total_job_skills > 0:
            keyword_coverage = int(round((len(matched_skills) / total_job_skills) * 100))
        else:
            keyword_coverage = 80  # Default baseline if no explicit skills extracted

        # Compute Text Cosine Similarity
        combined_job_text = f"{job_title} {job_description} {' '.join(all_job_skills_dict.values())}"
        cosine_sim = self.compute_tfidf_cosine_similarity(cv_text, combined_job_text)

        # Scale cosine similarity (typically 0.1 - 0.7 for resume text) to 0-100 range
        text_sim_score = min(100, int(round(cosine_sim * 160 + 20)))

        # Sub-signal Category Scores
        category_scores = {
            'domain_craft': self.evaluate_category_score(cv_text, 'domain_craft'),
            'collaboration': self.evaluate_category_score(cv_text, 'collaboration'),
            'leadership': self.evaluate_category_score(cv_text, 'leadership'),
            'accessibility': self.evaluate_category_score(cv_text, 'accessibility'),
        }

        avg_category = sum(category_scores.values()) / len(category_scores)

        # Composite Match Score Calculation (US-09)
        composite = (keyword_coverage * 0.40) + (text_sim_score * 0.40) + (avg_category * 0.20)
        final_match_score = max(10, min(99, int(round(composite))))

        # Strengths & Gaps
        strengths: List[str] = []
        gaps: List[str] = []
        recommendations: List[str] = []

        if matched_skills:
            strengths.append(f"Strong overlap in core technical skills: {', '.join(matched_skills[:4])}")
        if category_scores['domain_craft'] >= 80:
            strengths.append("Clear technical & domain craft evidence across work history")
        if category_scores['collaboration'] >= 80:
            strengths.append("Strong cross-functional collaboration and teamwork signals")

        if not strengths:
            strengths.append("Clean document structure and readable profile presentation")

        if missing_skills:
            gaps.append(f"Missing key required skills: {', '.join(missing_skills[:4])}")
            recommendations.append(f"Add explicit experience or project mentions for: {', '.join(missing_skills[:3])}")

        if category_scores['leadership'] < 70:
            gaps.append("Limited ownership or project leadership indicators detected")
            recommendations.append("Highlight ownership, decision-making, or project lead responsibilities")

        if category_scores['accessibility'] < 70:
            recommendations.append("Incorporate industry standards, quality metrics, or accessibility best practices")

        if not recommendations:
            recommendations.append("Quantify key project achievements with measurable metrics (%, $, scale)")

        return MatchEvaluationResult(
            match_score=final_match_score,
            keyword_coverage=keyword_coverage,
            category_scores=category_scores,
            skills_matched=matched_skills,
            skills_missing=missing_skills,
            strengths=strengths,
            gaps=gaps,
            recommendations=recommendations,
        )


def match_cv_to_job(
    cv: CandidateCV,
    job_title: str,
    job_description: str,
    required_skills: Optional[List[str]] = None,
    job_instance: Optional[JobRequirement] = None
) -> CVJobMatch:
    """
    High-level service helper to run semantic matching and persist result in CVJobMatch model.
    """
    matcher = CVJobSemanticMatcher()
    res = matcher.evaluate_match(
        cv=cv,
        job_title=job_title,
        job_description=job_description,
        required_skills=required_skills
    )

    company = job_instance.company if job_instance else 'CareerFlow Client'

    match_record, _ = CVJobMatch.objects.update_or_create(
        cv=cv,
        job=job_instance,
        job_title=job_title,
        defaults={
            'company': company,
            'job_description': job_description,
            'match_score': res.match_score,
            'keyword_coverage': res.keyword_coverage,
            'category_scores': res.category_scores,
            'skills_matched': res.skills_matched,
            'skills_missing': res.skills_missing,
            'strengths': res.strengths,
            'gaps': res.gaps,
            'recommendations': res.recommendations,
        }
    )

    return match_record
