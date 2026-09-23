"""
CV Feedback & Scoring Service (US-08).
Evaluates parsed candidate CVs against professional rubrics:
- Formatting & Section Completeness (Weight 20%)
- Keyword Strength & Action Verbs (Weight 30%)
- Clarity & Quantifiable Impact (Weight 30%)
- Experience & Education Completeness (Weight 20% - 10% each)

Generates an overall composite score (0-100) and top 3 actionable recommendations.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from apps.cv.models import CandidateCV, ParsedCV, CVFeedback
from apps.cv.services.pipeline import default_pipeline

logger = logging.getLogger(__name__)

# Action verbs strongly correlated with high-impact resumes
ACTION_VERBS = [
    'accelerated', 'accomplished', 'achieved', 'administered', 'advanced',
    'analyzed', 'architected', 'automated', 'built', 'championed',
    'collaborated', 'conducted', 'consolidated', 'constructed', 'created',
    'decreased', 'delivered', 'deployed', 'designed', 'developed',
    'directed', 'doubled', 'eliminated', 'engineered', 'enhanced',
    'established', 'executed', 'expanded', 'expedited', 'formulated',
    'generated', 'governed', 'guided', 'implemented', 'improved',
    'increased', 'initiated', 'innovated', 'integrated', 'invented',
    'launched', 'led', 'leveraged', 'managed', 'maximized',
    'mentored', 'minimized', 'modernized', 'negotiated', 'optimized',
    'orchestrated', 'organized', 'overhauled', 'pioneered', 'planned',
    'produced', 'programmed', 'rearchitected', 'reduced', 'refactored',
    'resolved', 'revamped', 'revitalized', 'saved', 'scaled',
    'simplified', 'spearheaded', 'standardized', 'streamlined', 'strengthened',
    'structured', 'succeeded', 'surpassed', 'trained', 'transformed',
    'upgraded', 'validated', 'yielded'
]

# Section headers standard in professional resumes
SECTION_PATTERNS = {
    'summary': re.compile(
        r'\b(summary|professional\s+summary|profile|about\s+me|career\s+objective|objective|executive\s+summary)\b',
        re.IGNORECASE
    ),
    'skills': re.compile(
        r'\b(skills|technical\s+skills|core\s+competencies|technologies|tools\s+(&|and)\s+technologies|tech\s+stack|competencies)\b',
        re.IGNORECASE
    ),
    'experience': re.compile(
        r'\b(experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history|internships?|career\s+history)\b',
        re.IGNORECASE
    ),
    'education': re.compile(
        r'\b(education|academic\s+background|academics|qualifications|degrees?|educational\s+history)\b',
        re.IGNORECASE
    ),
    'contact': re.compile(
        r'\b(contact|email|phone|linkedin|github|portfolio|address|mobile)\b',
        re.IGNORECASE
    ),
}

# Regex to detect measurable metrics: percentages, currency, multipliers, metrics
PERCENTAGE_REGEX = re.compile(r'\b\d+(?:\.\d+)?%')

CURRENCY_REGEX = re.compile(r'[\$€£]\s*\d+(?:,\d+)*(?:\.\d+)?(?:\s*[kKmMbB](?:illion)?)?\b')
MULTIPLIER_REGEX = re.compile(r'\b\d+(?:\.\d+)?\s*[xX]\b|\b\d+\s*\+\s*(?:years?|yrs?|users?|clients?|customers?|projects?)\b')
MAGNITUDE_NUMBERS_REGEX = re.compile(
    r'\b(?:\d{2,}|\d+(?:,\d{3})+|\d+(?:\.\d+)?\s*[kKmMbB])\s*(?:\w+\s+){0,2}(?:users|clients|requests|queries|downloads|records|visitors|endpoints|dollars|euros|lines|tests|features|commits|transactions)\b',
    re.IGNORECASE
)
GENERAL_METRIC_PHRASES = re.compile(
    r'\b(?:reduced|reducing|reduces|increased|increasing|increases|improved|improving|improves|boosted|boosting|boosts|saved|saving|saves|scaled|scaling|accelerated|accelerating|lowered|lowering|enhanced|enhancing|expanded|expanding)\s+(?:by\s+)?(?:\d+(?:\.\d+)?%?|\$[\d,]+|\d+\s*[kKmM]?)',
    re.IGNORECASE
)


@dataclass
class FormattingEvaluation:
    score: int
    detected_sections: List[str]
    missing_sections: List[str]
    has_dense_paragraphs: bool
    word_count: int
    paragraph_count: int


@dataclass
class KeywordEvaluation:
    score: int
    skills_count: int
    action_verbs_found: List[str]
    action_verbs_count: int
    action_verb_diversity: int


@dataclass
class ClarityEvaluation:
    score: int
    metrics_count: int
    metric_samples: List[str]
    bullet_count: int


@dataclass
class ExperienceEducationEvaluation:
    experience_score: int
    education_score: int
    experience_count: int
    education_count: int


class CVScorer:
    """
    Rubric-based CV Scorer and Feedback Engine.
    """

    def evaluate_formatting(self, raw_text: str) -> FormattingEvaluation:
        """
        US-08-T2: Evaluate document structure, section completeness, and paragraph density.
        """
        text = raw_text or ""
        words = text.split()
        word_count = len(words)

        # Detect presence of standard sections
        detected = []
        missing = []
        for sec_name, pattern in SECTION_PATTERNS.items():
            if pattern.search(text):
                detected.append(sec_name)
            else:
                missing.append(sec_name)

        # Check for dense paragraphs (> 150 words)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        has_dense_paragraphs = False
        dense_count = 0
        for p in paragraphs:
            p_words = len(p.split())
            if p_words > 150:
                has_dense_paragraphs = True
                dense_count += 1

        # Base score starts at 100
        score = 100

        # Section coverage (up to 5 sections, 10 pts per missing section)
        score -= (len(missing) * 10)

        # Word count adjustments
        if word_count < 40:
            score -= 30  # Severely sparse CV
        elif word_count < 70:
            score -= 10  # Very brief CV
        elif word_count > 1800:
            score -= 10  # Excessively verbose

        # Dense paragraph penalty
        if dense_count > 0:
            score -= min(20, dense_count * 8)

        # Clamp between 20 and 100
        score = max(20, min(100, score))

        return FormattingEvaluation(
            score=score,
            detected_sections=detected,
            missing_sections=missing,
            has_dense_paragraphs=has_dense_paragraphs,
            word_count=word_count,
            paragraph_count=len(paragraphs),
        )

    def evaluate_keywords(self, raw_text: str, skills: List[str]) -> KeywordEvaluation:
        """
        US-08-T3: Evaluate keyword richness, tech skills count, and action verb frequency.
        """
        text = (raw_text or "").lower()
        skills = skills or []
        skills_count = len(skills)

        # Search for action verbs
        action_verbs_found = set()
        total_action_count = 0

        for verb in ACTION_VERBS:
            matches = re.findall(r'\b' + re.escape(verb) + r'\b', text)
            if matches:
                action_verbs_found.add(verb)
                total_action_count += len(matches)

        # Score calculation:
        # 1. Technical skills (50% of keyword score):
        if skills_count >= 8:
            skill_sub = 50
        elif skills_count >= 6:
            skill_sub = 45
        elif skills_count >= 4:
            skill_sub = 38
        elif skills_count >= 2:
            skill_sub = 28
        elif skills_count >= 1:
            skill_sub = 20
        else:
            skill_sub = 10

        # 2. Action verbs (50% of keyword score):
        unique_verbs = len(action_verbs_found)
        if unique_verbs >= 5:
            action_sub = 50
        elif unique_verbs >= 3:
            action_sub = 42
        elif unique_verbs >= 2:
            action_sub = 32
        elif unique_verbs >= 1:
            action_sub = 22
        else:
            action_sub = 10

        score = max(20, min(100, skill_sub + action_sub))

        return KeywordEvaluation(
            score=score,
            skills_count=skills_count,
            action_verbs_found=sorted(list(action_verbs_found)),
            action_verbs_count=total_action_count,
            action_verb_diversity=unique_verbs,
        )

    def evaluate_clarity_and_impact(self, raw_text: str) -> ClarityEvaluation:
        """
        US-08-T3: Detect measurable metrics (percentages, numbers, currency) and quantifiable achievements.
        """
        text = raw_text or ""

        # Collect metrics
        metric_samples = []

        percentages = PERCENTAGE_REGEX.findall(text)
        metric_samples.extend(percentages[:4])

        currencies = CURRENCY_REGEX.findall(text)
        metric_samples.extend(currencies[:3])

        multipliers = MULTIPLIER_REGEX.findall(text)
        metric_samples.extend(multipliers[:3])

        magnitude_matches = MAGNITUDE_NUMBERS_REGEX.findall(text)
        metric_samples.extend(magnitude_matches[:3])

        phrase_matches = GENERAL_METRIC_PHRASES.findall(text)
        metric_samples.extend(phrase_matches[:3])

        unique_samples = list(dict.fromkeys(metric_samples))
        total_metrics = len(percentages) + len(currencies) + len(multipliers) + len(magnitude_matches) + len(phrase_matches)

        # Bullet count approximation
        bullet_count = len(re.findall(r'(?m)^[\s]*[•\-\*]\s+', text))

        # Scoring:
        # Resumes with 3+ quantifiable metrics receive 88-100 pts
        if total_metrics >= 4:
            score = 95
        elif total_metrics >= 3:
            score = 88
        elif total_metrics >= 2:
            score = 78
        elif total_metrics >= 1:
            score = 68
        else:
            score = 42

        # Bonus for bulleted readability
        if bullet_count >= 3:
            score = min(100, score + 5)

        return ClarityEvaluation(
            score=score,
            metrics_count=total_metrics,
            metric_samples=unique_samples[:8],
            bullet_count=bullet_count,
        )



    def evaluate_experience_and_education(
        self,
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        raw_text: str = ""
    ) -> ExperienceEducationEvaluation:
        """
        Evaluate completeness and depth of employment and degree records.
        """
        exp_list = experience or []
        edu_list = education or []

        # 1. Experience score
        exp_score = 60
        if len(exp_list) >= 3:
            exp_score = 95
        elif len(exp_list) == 2:
            exp_score = 88
        elif len(exp_list) == 1:
            exp_score = 78
        else:
            # Fallback check if text has experience keywords
            if re.search(r'\b(worked|intern|developer|engineer|lead|specialist|manager|analyst)\b', raw_text, re.IGNORECASE):
                exp_score = 65
            else:
                exp_score = 45

        # 2. Education score
        edu_score = 60
        if len(edu_list) >= 2:
            edu_score = 95
        elif len(edu_list) == 1:
            # Check if degree and institution are present
            first = edu_list[0]
            if first.get('degree') and first.get('institution'):
                edu_score = 90
            else:
                edu_score = 78
        else:
            if re.search(r'\b(bachelor|master|bsc|msc|university|college|phd|diploma)\b', raw_text, re.IGNORECASE):
                edu_score = 65
            else:
                edu_score = 45

        return ExperienceEducationEvaluation(
            experience_score=exp_score,
            education_score=edu_score,
            experience_count=len(exp_list),
            education_count=len(edu_list),
        )

    def calculate_composite_score(
        self,
        formatting_score: int,
        keyword_score: int,
        clarity_score: int,
        experience_score: int,
        education_score: int,
    ) -> int:
        """
        US-08 Composite Score:
        - Formatting & Structure: 20%
        - Keyword Strength: 30%
        - Clarity & Measurable Impact: 30%
        - Experience Completeness: 10%
        - Education Fit: 10%
        """
        composite = (
            0.20 * formatting_score +
            0.30 * keyword_score +
            0.30 * clarity_score +
            0.10 * experience_score +
            0.10 * education_score
        )
        return max(0, min(100, round(composite)))

    def generate_suggestions(
        self,
        fmt: FormattingEvaluation,
        kw: KeywordEvaluation,
        clar: ClarityEvaluation,
        exp_edu: ExperienceEducationEvaluation,
    ) -> List[str]:
        """
        US-08-T1 & T3: Dynamic suggestions engine returning exactly 3 prioritized actionable edits.
        """
        candidates: List[tuple[int, str]] = []  # (priority, recommendation_string)

        # 1. Measurable metrics (Priority 1 if completely missing, 2 if low)
        if clar.metrics_count == 0:
            candidates.append((
                1,
                "Quantify your results with measurable percentages, metrics, or figures (e.g., 'improved API response latency by 35%')."
            ))
        elif clar.metrics_count < 2:
            candidates.append((
                3,
                "Add more quantifiable business metrics to your achievements (such as user counts, percentage improvements, or delivery times)."
            ))

        # 2. Skills count & keywords (Priority 2)
        if kw.skills_count < 5:
            candidates.append((
                2,
                "Expand your skills section with core languages, industry frameworks, and tools to boost your ATS keyword visibility."
            ))

        # 3. Action verbs (Priority 4)
        if kw.action_verb_diversity < 4:
            candidates.append((
                4,
                "Begin your experience bullet points with strong action verbs like 'Engineered', 'Optimized', or 'Spearheaded' rather than passive phrasing."
            ))

        # 4. Missing standard sections (Priority 5)
        if 'experience' in fmt.missing_sections:
            candidates.append((
                5,
                "Add an explicit 'Work Experience' or 'Projects' section heading to help recruiters and ATS systems parse your background."
            ))
        elif 'skills' in fmt.missing_sections:
            candidates.append((
                6,
                "Include a dedicated 'Technical Skills' section heading to highlight your core competencies."
            ))
        elif 'education' in fmt.missing_sections:
            candidates.append((
                7,
                "Add an 'Education' section heading specifying your degree, institution, and graduation year."
            ))
        elif 'summary' in fmt.missing_sections:
            candidates.append((
                8,
                "Include a punchy 2-3 line professional summary highlighting your key strengths and career trajectory."
            ))

        # 5. Formatting & dense paragraphs (Priority 9)
        if fmt.has_dense_paragraphs:
            candidates.append((
                9,
                "Break dense paragraphs (>150 words) into concise, 2-3 line bullet points for enhanced recruiter readability."
            ))
        elif fmt.word_count < 150:
            candidates.append((
                10,
                "Expand your CV with more details on project scope, technical challenges overcome, and business outcomes."
            ))

        # 6. Experience & Education completeness (Priority 11)
        if exp_edu.experience_count == 0:
            candidates.append((
                11,
                "Detail your recent roles or academic capstones with company/team name, title, and key project contributions."
            ))
        if exp_edu.education_count == 0:
            candidates.append((
                12,
                "Specify your formal degree title, major, university, and graduation year in your education section."
            ))

        # Fallback high-performing recommendations if the CV is already strong
        candidates.append((
            20,
            "Tailor your technical keywords and project bullet points directly to align with specific target job postings."
        ))
        candidates.append((
            21,
            "Group your technical skills into distinct subcategories (e.g., Languages, Frameworks, Cloud & DevOps, Databases) for faster visual scanning."
        ))
        candidates.append((
            22,
            "Position your most impressive, metric-backed accomplishment in the top third of your resume where it gets noticed first."
        ))
        candidates.append((
            23,
            "Ensure hyperlinks to your GitHub profile, LinkedIn, and live project demos are clickable and up to date."
        ))

        # Sort by priority asc and pick top 3 unique suggestions
        candidates.sort(key=lambda x: x[0])

        selected = []
        seen = set()
        for _, text in candidates:
            if text not in seen:
                seen.add(text)
                selected.append(text)
            if len(selected) == 3:
                break

        return selected

    def score(
        self,
        raw_text: str,
        skills: Optional[List[str]] = None,
        experience: Optional[List[Dict[str, Any]]] = None,
        education: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full scoring rubric and return structured results.
        """
        skills = skills or []
        experience = experience or []
        education = education or []

        fmt_eval = self.evaluate_formatting(raw_text)
        kw_eval = self.evaluate_keywords(raw_text, skills)
        clar_eval = self.evaluate_clarity_and_impact(raw_text)
        exp_edu_eval = self.evaluate_experience_and_education(experience, education, raw_text=raw_text)

        overall_score = self.calculate_composite_score(
            formatting_score=fmt_eval.score,
            keyword_score=kw_eval.score,
            clarity_score=clar_eval.score,
            experience_score=exp_edu_eval.experience_score,
            education_score=exp_edu_eval.education_score,
        )

        suggestions = self.generate_suggestions(fmt_eval, kw_eval, clar_eval, exp_edu_eval)

        signal_breakdown = {
            'formatting': {
                'score': fmt_eval.score,
                'weight': '20%',
                'word_count': fmt_eval.word_count,
                'detected_sections': fmt_eval.detected_sections,
                'missing_sections': fmt_eval.missing_sections,
                'has_dense_paragraphs': fmt_eval.has_dense_paragraphs,
            },
            'keyword_strength': {
                'score': kw_eval.score,
                'weight': '30%',
                'skills_count': kw_eval.skills_count,
                'action_verbs_count': kw_eval.action_verbs_count,
                'action_verbs_found': kw_eval.action_verbs_found[:10],
            },
            'clarity_impact': {
                'score': clar_eval.score,
                'weight': '30%',
                'metrics_count': clar_eval.metrics_count,
                'metric_samples': clar_eval.metric_samples,
                'bullet_count': clar_eval.bullet_count,
            },
            'experience': {
                'score': exp_edu_eval.experience_score,
                'weight': '10%',
                'records_count': exp_edu_eval.experience_count,
            },
            'education': {
                'score': exp_edu_eval.education_score,
                'weight': '10%',
                'records_count': exp_edu_eval.education_count,
            },
        }

        return {
            'overall_score': overall_score,
            'formatting_score': fmt_eval.score,
            'clarity_score': clar_eval.score,
            'keyword_strength_score': kw_eval.score,
            'experience_score': exp_edu_eval.experience_score,
            'education_score': exp_edu_eval.education_score,
            'suggestions': suggestions,
            'signal_breakdown': signal_breakdown,
        }


# Default scorer singleton
default_scorer = CVScorer()


def generate_cv_feedback(candidate_cv: CandidateCV) -> CVFeedback:
    """
    Orchestrates parsing (if needed) and generates/persists CVFeedback record.
    Fulfills US-08-T1, T2, T3, T5.
    """
    # 1. Ensure ParsedCV exists for this CV
    parsed_cv = getattr(candidate_cv, 'parsed_data', None)
    if not parsed_cv:
        try:
            parsed_cv = ParsedCV.objects.filter(cv=candidate_cv).first()
        except Exception:
            parsed_cv = None

    if not parsed_cv:
        # Trigger parsing pipeline automatically (US-07 integration)
        logger.info(f"Auto-triggering extraction pipeline for CV ID {candidate_cv.id}")
        result = default_pipeline.process_candidate_cv(candidate_cv)
        parsed_cv, _ = ParsedCV.objects.update_or_create(
            cv=candidate_cv,
            defaults={
                'raw_text': result.raw_text,
                'skills': result.skills,
                'education': result.education,
                'experience': result.experience,
            }
        )

    # 2. Score parsed CV
    scoring_result = default_scorer.score(
        raw_text=parsed_cv.raw_text,
        skills=parsed_cv.skills,
        experience=parsed_cv.experience,
        education=parsed_cv.education,
    )

    # 3. Save or update CVFeedback
    feedback, _ = CVFeedback.objects.update_or_create(
        cv=candidate_cv,
        defaults={
            'overall_score': scoring_result['overall_score'],
            'formatting_score': scoring_result['formatting_score'],
            'clarity_score': scoring_result['clarity_score'],
            'keyword_strength_score': scoring_result['keyword_strength_score'],
            'experience_score': scoring_result['experience_score'],
            'education_score': scoring_result['education_score'],
            'suggestions': scoring_result['suggestions'],
            'signal_breakdown': scoring_result['signal_breakdown'],
        }
    )

    return feedback
