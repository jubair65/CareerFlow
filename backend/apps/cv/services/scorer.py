"""
CV Feedback & Scoring Service (US-08).
Evaluates parsed candidate CVs against professional rubrics:
- Formatting & Section Completeness (Weight 20%)
- Keyword Strength & Action Verbs (Weight 30%)
- Clarity & Quantifiable Impact (Weight 30%)
- Experience & Education Completeness (Weight 20% - 10% each)

Generates an overall composite score (0-100) and up to 6 prioritised,
CV-content-aware actionable recommendations.

Improvements over v1:
- Smooth linear interpolation scoring (no cliff jumps)
- Weak passive-voice phrase detection
- Suggestions reference actual content from the candidate's CV
- Up to 6 suggestions shown (grouped by category)
- Role-specific keyword boost profiles
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from apps.cv.models import CandidateCV, ParsedCV, CVFeedback
from apps.cv.services.pipeline import default_pipeline
from apps.cv.services.gemini_suggestions import generate_gemini_suggestions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Action verbs strongly correlated with high-impact resumes
# ---------------------------------------------------------------------------
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
    'upgraded', 'validated', 'yielded',
]

# ---------------------------------------------------------------------------
# Weak passive phrases that undermine resume impact
# ---------------------------------------------------------------------------
WEAK_PHRASE_PATTERNS = re.compile(
    r'\b(responsible for|worked on|helped with|assisted in|participated in'
    r'|involved in|tasked with|duties included|duties include'
    r'|helped to|tried to|attempted to|was part of)\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Section headers standard in professional resumes
# ---------------------------------------------------------------------------
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
        r'\b(experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history|internships?|career\s+history|projects?)\b',
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

# ---------------------------------------------------------------------------
# Metric detection regexes
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Role-specific keyword boost profiles
# ---------------------------------------------------------------------------
ROLE_PROFILES: Dict[str, Dict[str, Any]] = {
    'frontend': {
        'labels': ['frontend', 'front-end', 'front end', 'ui', 'ux', 'react developer', 'vue developer', 'angular developer'],
        'bonus_skills': ['React', 'Next.js', 'TypeScript', 'CSS', 'TailwindCSS', 'GraphQL', 'Redux', 'Zustand', 'Vite', 'Figma'],
        'bonus_verbs': ['designed', 'implemented', 'built', 'optimized'],
    },
    'backend': {
        'labels': ['backend', 'back-end', 'back end', 'api developer', 'server-side', 'django developer', 'node developer'],
        'bonus_skills': ['Python', 'Django', 'FastAPI', 'Node.js', 'PostgreSQL', 'Redis', 'Docker', 'REST', 'JWT', 'SQL'],
        'bonus_verbs': ['engineered', 'designed', 'deployed', 'optimized', 'scaled'],
    },
    'fullstack': {
        'labels': ['full stack', 'fullstack', 'full-stack'],
        'bonus_skills': ['React', 'Node.js', 'Python', 'PostgreSQL', 'Docker', 'TypeScript', 'REST', 'AWS'],
        'bonus_verbs': ['built', 'architected', 'deployed', 'integrated'],
    },
    'devops': {
        'labels': ['devops', 'sre', 'site reliability', 'platform engineer', 'cloud engineer', 'infrastructure'],
        'bonus_skills': ['Docker', 'Kubernetes', 'Terraform', 'AWS', 'CI/CD', 'Linux', 'Prometheus', 'Grafana', 'Ansible', 'Helm'],
        'bonus_verbs': ['automated', 'deployed', 'orchestrated', 'optimized', 'migrated'],
    },
    'data_science': {
        'labels': ['data scientist', 'data science', 'machine learning', 'ml engineer', 'ai engineer', 'data analyst'],
        'bonus_skills': ['Python', 'Pandas', 'NumPy', 'Scikit-Learn', 'TensorFlow', 'PyTorch', 'SQL', 'Matplotlib', 'Machine Learning'],
        'bonus_verbs': ['analyzed', 'modeled', 'trained', 'evaluated', 'built', 'optimized'],
    },
    'mobile': {
        'labels': ['mobile developer', 'android developer', 'ios developer', 'flutter developer', 'react native developer'],
        'bonus_skills': ['Flutter', 'React Native', 'Swift', 'Kotlin', 'Android SDK', 'Dart', 'SwiftUI', 'Firebase'],
        'bonus_verbs': ['developed', 'built', 'shipped', 'published', 'designed'],
    },
    'data_engineering': {
        'labels': ['data engineer', 'etl', 'pipeline engineer', 'analytics engineer'],
        'bonus_skills': ['Apache Spark', 'PySpark', 'dbt', 'Airflow', 'Kafka', 'Snowflake', 'BigQuery', 'Redshift', 'Python', 'SQL'],
        'bonus_verbs': ['built', 'designed', 'automated', 'optimized', 'integrated'],
    },
}


def detect_role_profile(raw_text: str) -> Optional[str]:
    """
    Detect the likely target role from the CV text to apply role-specific scoring.
    Returns the matched profile key (e.g. 'frontend', 'devops') or None.
    """
    text_lower = raw_text.lower()
    for profile_key, profile in ROLE_PROFILES.items():
        for label in profile['labels']:
            if label in text_lower:
                return profile_key
    return None


# ---------------------------------------------------------------------------
# Dataclasses for evaluation results
# ---------------------------------------------------------------------------

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
    weak_phrases_found: List[str]
    role_profile: Optional[str]
    role_bonus_applied: bool


@dataclass
class ClarityEvaluation:
    score: int
    metrics_count: int
    metric_samples: List[str]
    bullet_count: int
    weak_bullet_examples: List[str]


@dataclass
class ExperienceEducationEvaluation:
    experience_score: int
    education_score: int
    experience_count: int
    education_count: int


# ---------------------------------------------------------------------------
# Helper: smooth linear scoring (no cliff jumps)
# ---------------------------------------------------------------------------

def _linear_score(value: int, breakpoints: List[Tuple[int, int]], clamp_min: int = 20, clamp_max: int = 100) -> int:
    """
    Interpolate a score smoothly given a sorted list of (threshold, score) breakpoints.
    Between two breakpoints the score scales linearly.
    """
    if not breakpoints:
        return clamp_min

    # Below the first breakpoint
    if value <= breakpoints[0][0]:
        return max(clamp_min, breakpoints[0][1])

    # Above the last breakpoint
    if value >= breakpoints[-1][0]:
        return min(clamp_max, breakpoints[-1][1])

    # Linear interpolation between adjacent breakpoints
    for i in range(len(breakpoints) - 1):
        t1, s1 = breakpoints[i]
        t2, s2 = breakpoints[i + 1]
        if t1 <= value <= t2:
            ratio = (value - t1) / (t2 - t1)
            interpolated = s1 + ratio * (s2 - s1)
            return max(clamp_min, min(clamp_max, round(interpolated)))

    return clamp_min


# ---------------------------------------------------------------------------
# Bullet-level analysis helpers
# ---------------------------------------------------------------------------

def _extract_bullet_lines(raw_text: str) -> List[str]:
    """Extract bullet-point lines from raw CV text."""
    return [
        line.strip()
        for line in raw_text.splitlines()
        if re.match(r'^[\s]*[•\-\*]\s+', line) and len(line.strip()) > 5
    ]


def _find_weak_bullet_examples(raw_text: str) -> List[str]:
    """
    Find bullet lines that start with a weak passive phrase or lack any
    action verb. Returns up to 2 examples (truncated to 80 chars).
    """
    bullets = _extract_bullet_lines(raw_text)
    weak = []
    for bullet in bullets:
        clean = re.sub(r'^[\s•\-\*]+', '', bullet).strip()
        if WEAK_PHRASE_PATTERNS.match(clean):
            snippet = clean[:80] + ('…' if len(clean) > 80 else '')
            weak.append(snippet)
            if len(weak) == 2:
                break
    return weak


def _find_metric_free_bullet_examples(raw_text: str) -> List[str]:
    """
    Find bullet lines that contain an action verb but zero numeric metrics.
    Returns up to 2 examples as improvement targets.
    """
    bullets = _extract_bullet_lines(raw_text)
    examples = []
    action_verb_re = re.compile(
        r'\b(' + '|'.join(ACTION_VERBS) + r')\b', re.IGNORECASE
    )
    number_re = re.compile(r'\d')

    for bullet in bullets:
        has_verb = bool(action_verb_re.search(bullet))
        has_number = bool(number_re.search(bullet))
        if has_verb and not has_number:
            clean = re.sub(r'^[\s•\-\*]+', '', bullet).strip()
            snippet = clean[:80] + ('…' if len(clean) > 80 else '')
            examples.append(snippet)
            if len(examples) == 2:
                break
    return examples


# ---------------------------------------------------------------------------
# Main scorer class
# ---------------------------------------------------------------------------

class CVScorer:
    """
    Rubric-based CV Scorer and Feedback Engine (improved v2).
    """

    def evaluate_formatting(self, raw_text: str) -> FormattingEvaluation:
        """
        US-08-T2: Evaluate document structure, section completeness, and paragraph density.
        """
        text = raw_text or ''
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
            if len(p.split()) > 150:
                has_dense_paragraphs = True
                dense_count += 1

        # Base score: 100, minus penalties
        score = 100

        # Missing section penalty (10 pts each)
        score -= len(missing) * 10

        # Word count — smooth scoring with linear interpolation
        if word_count < 40:
            score -= 30
        elif word_count < 100:
            # Linear: 100 words → no penalty, 40 words → 10 penalty
            penalty = round(10 * (1 - (word_count - 40) / 60))
            score -= penalty
        elif word_count > 1800:
            score -= 10

        # Dense paragraph penalty
        if dense_count > 0:
            score -= min(20, dense_count * 8)

        score = max(20, min(100, score))

        return FormattingEvaluation(
            score=score,
            detected_sections=detected,
            missing_sections=missing,
            has_dense_paragraphs=has_dense_paragraphs,
            word_count=word_count,
            paragraph_count=len(paragraphs),
        )

    def evaluate_keywords(
        self,
        raw_text: str,
        skills: List[str],
        role_profile: Optional[str] = None,
    ) -> KeywordEvaluation:
        """
        US-08-T3: Evaluate keyword richness, tech skills count, action verb frequency,
        weak phrase detection, and optional role-specific bonus.
        """
        text = (raw_text or '').lower()
        skills = skills or []
        skills_count = len(skills)

        # Search for action verbs
        action_verbs_found: set = set()
        total_action_count = 0
        for verb in ACTION_VERBS:
            matches = re.findall(r'\b' + re.escape(verb) + r'\b', text)
            if matches:
                action_verbs_found.add(verb)
                total_action_count += len(matches)

        # Detect weak passive phrases
        weak_matches = WEAK_PHRASE_PATTERNS.findall(raw_text or '')
        weak_phrases_found = list(set(w.lower() for w in weak_matches))

        # --- SMOOTH skill sub-score (50 pts max) ---
        # Linear: 0 skills → 10, 10+ skills → 50
        skill_sub = _linear_score(
            skills_count,
            [(0, 10), (2, 22), (4, 34), (6, 42), (8, 48), (10, 50)],
            clamp_min=10, clamp_max=50,
        )

        # --- SMOOTH action verb sub-score (50 pts max) ---
        unique_verbs = len(action_verbs_found)
        action_sub = _linear_score(
            unique_verbs,
            [(0, 10), (1, 20), (2, 30), (3, 38), (5, 45), (7, 50)],
            clamp_min=10, clamp_max=50,
        )

        # Weak phrase penalty (up to −10)
        weak_penalty = min(10, len(weak_phrases_found) * 3)
        action_sub = max(10, action_sub - weak_penalty)

        score = max(20, min(100, skill_sub + action_sub))

        # Role-specific bonus: +5 if candidate has 3+ bonus skills for their role
        role_bonus_applied = False
        if role_profile and role_profile in ROLE_PROFILES:
            profile = ROLE_PROFILES[role_profile]
            bonus_skills_lower = [s.lower() for s in profile['bonus_skills']]
            candidate_skills_lower = [s.lower() for s in skills]
            matching_bonus = sum(1 for s in candidate_skills_lower if s in bonus_skills_lower)
            if matching_bonus >= 3:
                score = min(100, score + 5)
                role_bonus_applied = True

        return KeywordEvaluation(
            score=score,
            skills_count=skills_count,
            action_verbs_found=sorted(list(action_verbs_found)),
            action_verbs_count=total_action_count,
            action_verb_diversity=unique_verbs,
            weak_phrases_found=weak_phrases_found,
            role_profile=role_profile,
            role_bonus_applied=role_bonus_applied,
        )

    def evaluate_clarity_and_impact(self, raw_text: str) -> ClarityEvaluation:
        """
        US-08-T3: Detect measurable metrics (percentages, numbers, currency) and
        quantifiable achievements. Also surfaces weak bullet examples.
        """
        text = raw_text or ''

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
        total_metrics = (
            len(percentages) + len(currencies) + len(multipliers)
            + len(magnitude_matches) + len(phrase_matches)
        )

        # Bullet count
        bullet_count = len(re.findall(r'(?m)^[\s]*[•\-\*]\s+', text))

        # --- SMOOTH clarity score ---
        # 0 metrics → 42, 6+ metrics → 98
        score = _linear_score(
            total_metrics,
            [(0, 42), (1, 60), (2, 72), (3, 82), (4, 90), (6, 98)],
            clamp_min=42, clamp_max=100,
        )

        # Bullet readability bonus
        if bullet_count >= 3:
            score = min(100, score + 4)

        # Find bullet examples that have no metric (for targeted suggestions)
        weak_bullet_examples = _find_metric_free_bullet_examples(text)

        return ClarityEvaluation(
            score=score,
            metrics_count=total_metrics,
            metric_samples=unique_samples[:8],
            bullet_count=bullet_count,
            weak_bullet_examples=weak_bullet_examples,
        )

    def evaluate_experience_and_education(
        self,
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        raw_text: str = '',
    ) -> ExperienceEducationEvaluation:
        """
        Evaluate completeness and depth of employment and degree records.
        Uses smooth linear scoring.
        """
        exp_list = experience or []
        edu_list = education or []

        # --- Experience score (smooth) ---
        exp_count = len(exp_list)
        if exp_count == 0:
            # Keyword fallback
            if re.search(r'\b(worked|intern|developer|engineer|lead|specialist|manager|analyst)\b', raw_text, re.IGNORECASE):
                exp_score = 65
            else:
                exp_score = 45
        else:
            exp_score = _linear_score(
                exp_count,
                [(1, 75), (2, 85), (3, 93), (4, 97)],
                clamp_min=75, clamp_max=97,
            )

        # --- Education score (smooth) ---
        edu_count = len(edu_list)
        if edu_count == 0:
            if re.search(r'\b(bachelor|master|bsc|msc|university|college|phd|diploma)\b', raw_text, re.IGNORECASE):
                edu_score = 65
            else:
                edu_score = 45
        else:
            # Check richness of first entry
            first = edu_list[0]
            has_degree = bool(first.get('degree'))
            has_institution = bool(first.get('institution') and first.get('institution') != 'Not Specified')
            has_year = bool(first.get('year'))
            richness = sum([has_degree, has_institution, has_year])
            base = _linear_score(edu_count, [(1, 78), (2, 92), (3, 97)], clamp_min=78, clamp_max=97)
            edu_score = min(97, base + richness * 2)

        return ExperienceEducationEvaluation(
            experience_score=exp_score,
            education_score=edu_score,
            experience_count=exp_count,
            education_count=edu_count,
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
            0.20 * formatting_score
            + 0.30 * keyword_score
            + 0.30 * clarity_score
            + 0.10 * experience_score
            + 0.10 * education_score
        )
        return max(0, min(100, round(composite)))

    def generate_suggestions(
        self,
        fmt: FormattingEvaluation,
        kw: KeywordEvaluation,
        clar: ClarityEvaluation,
        exp_edu: ExperienceEducationEvaluation,
        raw_text: str = '',
    ) -> List[str]:
        """
        US-08-T1 & T3: Dynamic, CV-content-aware suggestions engine.
        Returns up to 6 prioritised, actionable recommendations.
        Suggestions reference actual CV content where possible.
        """
        candidates: List[Tuple[int, str]] = []

        # ------------------------------------------------------------------
        # 1. Measurable metrics (highest priority if completely missing)
        # ------------------------------------------------------------------
        if clar.metrics_count == 0:
            if clar.weak_bullet_examples:
                example = clar.weak_bullet_examples[0]
                candidates.append((
                    1,
                    f"Add quantifiable results to your bullet points. "
                    f"For example, change \"{example}\" to include a metric like "
                    f"'…reduced load time by 40%' or '…serving 5,000 daily users'."
                ))
            else:
                candidates.append((
                    1,
                    "Quantify your results with measurable percentages, metrics, or figures "
                    "(e.g., 'improved API response latency by 35%' or 'reduced bug count by 60%')."
                ))
        elif clar.metrics_count < 3:
            if clar.weak_bullet_examples:
                example = clar.weak_bullet_examples[0]
                candidates.append((
                    3,
                    f"You have {clar.metrics_count} metric(s) — aim for at least 4-6. "
                    f"Start with: \"{example}\" — add a number (users, speed, percentage, cost)."
                ))
            else:
                candidates.append((
                    3,
                    f"You have {clar.metrics_count} quantifiable metric(s). "
                    "Add more measurable business results (user counts, percentage improvements, or delivery times)."
                ))

        # ------------------------------------------------------------------
        # 2. Weak passive phrases
        # ------------------------------------------------------------------
        if kw.weak_phrases_found:
            phrase_list = ', '.join(f'"{p}"' for p in kw.weak_phrases_found[:3])
            candidates.append((
                2,
                f"Replace weak passive phrases like {phrase_list} with strong action verbs. "
                "For example: 'Engineered', 'Optimized', 'Spearheaded', or 'Launched'."
            ))

        # ------------------------------------------------------------------
        # 3. Skills count & keywords
        # ------------------------------------------------------------------
        if kw.skills_count < 5:
            candidates.append((
                4,
                f"Only {kw.skills_count} technical skill(s) were detected. "
                "Expand your Skills section with core languages, frameworks, cloud platforms, "
                "and tools to boost your ATS keyword visibility."
            ))
        elif kw.skills_count < 8:
            candidates.append((
                6,
                f"You have {kw.skills_count} skills detected. "
                "Consider adding more domain-specific tools (e.g., testing frameworks, cloud services, or ORMs) "
                "to strengthen your technical profile."
            ))

        # ------------------------------------------------------------------
        # 4. Action verb diversity
        # ------------------------------------------------------------------
        if kw.action_verb_diversity < 3:
            candidates.append((
                5,
                f"Only {kw.action_verb_diversity} unique action verb(s) detected. "
                "Begin each experience bullet with a different strong action verb like "
                "'Engineered', 'Optimized', 'Delivered', 'Migrated', or 'Scaled' to show breadth."
            ))
        elif kw.action_verb_diversity < 5:
            candidates.append((
                7,
                f"You used {kw.action_verb_diversity} unique action verbs — aim for 6+. "
                "Vary your bullet openers to avoid repetition and demonstrate range."
            ))

        # ------------------------------------------------------------------
        # 5. Missing standard sections
        # ------------------------------------------------------------------
        if 'experience' in fmt.missing_sections:
            candidates.append((
                8,
                "Add an explicit 'Work Experience' or 'Projects' section heading to help "
                "recruiters and ATS systems parse your background correctly."
            ))
        if 'skills' in fmt.missing_sections:
            candidates.append((
                9,
                "Include a dedicated 'Technical Skills' section to highlight your core competencies. "
                "Group them by category (Languages, Frameworks, Cloud, Databases)."
            ))
        if 'education' in fmt.missing_sections:
            candidates.append((
                10,
                "Add an 'Education' section specifying your degree, institution, and graduation year."
            ))
        if 'summary' in fmt.missing_sections:
            candidates.append((
                11,
                "Include a punchy 2-3 line professional summary at the top. "
                "It's the first thing recruiters read — highlight your role, years of experience, and key strength."
            ))
        if 'contact' in fmt.missing_sections:
            candidates.append((
                12,
                "Ensure your contact details (email, phone, LinkedIn, GitHub) are clearly visible at the top of your CV."
            ))

        # ------------------------------------------------------------------
        # 6. Dense paragraphs / word count
        # ------------------------------------------------------------------
        if fmt.has_dense_paragraphs:
            candidates.append((
                13,
                "Break dense text blocks (>150 words) into concise, 2-3 line bullet points. "
                "Recruiters scan — not read. Bullets make your achievements immediately visible."
            ))
        elif fmt.word_count < 150:
            candidates.append((
                14,
                f"Your CV is brief ({fmt.word_count} words). "
                "Expand with more detail on project scope, technical challenges, team size, and outcomes."
            ))

        # ------------------------------------------------------------------
        # 7. Experience & Education completeness
        # ------------------------------------------------------------------
        if exp_edu.experience_count == 0:
            candidates.append((
                15,
                "Detail your recent roles or academic projects with company/team name, title, "
                "date range, and 2-3 bullet points of key contributions."
            ))
        if exp_edu.education_count == 0:
            candidates.append((
                16,
                "Specify your formal degree title, major, university name, and graduation year."
            ))

        # ------------------------------------------------------------------
        # 8. Role-specific tip
        # ------------------------------------------------------------------
        if kw.role_profile:
            profile = ROLE_PROFILES[kw.role_profile]
            bonus_skills_str = ', '.join(profile['bonus_skills'][:5])
            candidates.append((
                17,
                f"Your CV appears targeting a {kw.role_profile.replace('_', ' ').title()} role. "
                f"Make sure these high-value skills are prominently listed if you have them: {bonus_skills_str}."
            ))

        # ------------------------------------------------------------------
        # 9. Evergreen high-value recommendations (fallback)
        # ------------------------------------------------------------------
        candidates.append((
            20,
            "Tailor your technical keywords and project bullet points to align directly with each target job posting."
        ))
        candidates.append((
            21,
            "Group your technical skills into subcategories (Languages, Frameworks, Cloud & DevOps, Databases, Testing) for faster visual scanning."
        ))
        candidates.append((
            22,
            "Position your most impressive, metric-backed accomplishment in the top third of your CV where it gets noticed first."
        ))
        candidates.append((
            23,
            "Ensure hyperlinks to your GitHub profile, LinkedIn, and live project demos are clickable and up to date."
        ))

        # Sort by priority and pick top 3 unique suggestions (US-08 requirement)
        candidates.sort(key=lambda x: x[0])
        selected = []
        seen: set = set()
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
        Scores are always computed by the rule-based engine (fast, deterministic).
        Suggestions are generated by Gemini if the API key is configured,
        otherwise falls back to the rule-based suggestion engine.
        """
        skills = skills or []
        experience = experience or []
        education = education or []

        # Detect role before scoring (used for keyword bonus)
        role_profile = detect_role_profile(raw_text)

        fmt_eval = self.evaluate_formatting(raw_text)
        kw_eval = self.evaluate_keywords(raw_text, skills, role_profile=role_profile)
        clar_eval = self.evaluate_clarity_and_impact(raw_text)
        exp_edu_eval = self.evaluate_experience_and_education(experience, education, raw_text=raw_text)

        overall_score = self.calculate_composite_score(
            formatting_score=fmt_eval.score,
            keyword_score=kw_eval.score,
            clarity_score=clar_eval.score,
            experience_score=exp_edu_eval.experience_score,
            education_score=exp_edu_eval.education_score,
        )

        # --- Generate rule-based suggestions first (always used as fallback / Gemini context) ---
        rule_based_suggestions = self.generate_suggestions(
            fmt_eval, kw_eval, clar_eval, exp_edu_eval, raw_text=raw_text
        )

        # --- Attempt Gemini-powered suggestions (contextual, CV-specific) ---
        gemini_suggestions = generate_gemini_suggestions(
            raw_text=raw_text,
            overall_score=overall_score,
            formatting_score=fmt_eval.score,
            keyword_score=kw_eval.score,
            clarity_score=clar_eval.score,
            experience_score=exp_edu_eval.experience_score,
            education_score=exp_edu_eval.education_score,
            skills=skills,
            weak_phrases=kw_eval.weak_phrases_found,
            weak_bullets=clar_eval.weak_bullet_examples,
            rule_based_hints=rule_based_suggestions,
            role_profile=role_profile,
        )

        # Use Gemini if it returned valid suggestions; otherwise rule-based
        if gemini_suggestions and len(gemini_suggestions) >= 2:
            suggestions = gemini_suggestions
            suggestions_source = "gemini"
        else:
            suggestions = rule_based_suggestions
            suggestions_source = "rule-based"

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
                'weak_phrases_found': kw_eval.weak_phrases_found,
                'role_profile': kw_eval.role_profile,
                'role_bonus_applied': kw_eval.role_bonus_applied,
            },
            'clarity_impact': {
                'score': clar_eval.score,
                'weight': '30%',
                'metrics_count': clar_eval.metrics_count,
                'metric_samples': clar_eval.metric_samples,
                'bullet_count': clar_eval.bullet_count,
                'weak_bullet_examples': clar_eval.weak_bullet_examples,
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
            # Track which engine generated the suggestions
            'ai_suggestions_source': suggestions_source,
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


# ---------------------------------------------------------------------------
# Default scorer singleton
# ---------------------------------------------------------------------------
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
        if not result.success:
            raise ValueError(f"Unable to extract text from document: {result.error_message}")
        if not result.raw_text or not result.raw_text.strip():
            raise ValueError(
                "Unable to extract text from document. "
                "Ensure document is not password-protected or scanned as a raw image."
            )
        parsed_cv, _ = ParsedCV.objects.update_or_create(
            cv=candidate_cv,
            defaults={
                'raw_text': result.raw_text,
                'skills': result.skills,
                'education': result.education,
                'experience': result.experience,
            }
        )
    elif not parsed_cv.raw_text or not parsed_cv.raw_text.strip():
        raise ValueError(
            "Unable to extract text from document. "
            "Ensure document is not password-protected or scanned as a raw image."
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
