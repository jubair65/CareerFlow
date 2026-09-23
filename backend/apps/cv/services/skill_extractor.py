import os
import re
import json
from typing import List, Dict, Set, Any, Optional, Tuple

DEFAULT_TAXONOMY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'data',
    'skills_taxonomy.json'
)

# Canonical mapping for aliases and synonyms
CANONICAL_ALIASES = {
    'react.js': 'React',
    'reactjs': 'React',
    'node.js': 'Node.js',
    'nodejs': 'Node.js',
    'express.js': 'Express',
    'expressjs': 'Express',
    'vue.js': 'Vue',
    'vuejs': 'Vue',
    'nuxt.js': 'Nuxt.js',
    'nuxtjs': 'Nuxt.js',
    'golang': 'Go',
    'k8s': 'Kubernetes',
    'postgres': 'PostgreSQL',
    'postgresql': 'PostgreSQL',
    'tailwind css': 'TailwindCSS',
    'tailwindcss': 'TailwindCSS',
    'drf': 'Django REST Framework',
    'django rest framework': 'Django REST Framework',
    'amazon web services': 'AWS',
    'google cloud platform': 'GCP',
    'microsoft azure': 'Azure',
    'nlp': 'Natural Language Processing',
    'natural language processing': 'Natural Language Processing',
    'ml': 'Machine Learning',
    'machine learning': 'Machine Learning',
    'ai': 'Artificial Intelligence',
    'artificial intelligence': 'Artificial Intelligence',
    'rest': 'REST API',
    'restful api': 'REST API',
    'rest api': 'REST API',
    '.net core': '.NET Core',
}


class SkillExtractor:
    """
    Identifies and extracts technical and professional skills from raw text
    using taxonomy-based regex pattern matching.
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        self.taxonomy_path = taxonomy_path or DEFAULT_TAXONOMY_PATH
        self.taxonomy: Dict[str, List[str]] = self._load_taxonomy()
        self.skill_to_category: Dict[str, str] = {}
        # Stores tuples: (compiled_regex, canonical_name, category)
        self.compiled_patterns: List[Tuple[re.Pattern, str, str]] = []
        self._build_patterns()

    def _load_taxonomy(self) -> Dict[str, List[str]]:
        if os.path.exists(self.taxonomy_path):
            try:
                with open(self.taxonomy_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback default taxonomy if file is missing/unreadable
        return {
            'programming_languages': ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'PHP', 'SQL'],
            'frameworks': ['React', 'Django', 'FastAPI', 'Node.js', 'Next.js', 'Spring Boot', 'TailwindCSS'],
            'databases': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'SQLite'],
            'devops': ['Docker', 'Kubernetes', 'AWS', 'Git', 'CI/CD', 'Linux'],
        }

    def _build_patterns(self):
        """
        Compile regex patterns for all skills and aliases with appropriate boundaries:
        - Handle symbol-containing skills (C++, C#, .NET, Node.js, CI/CD)
        - Handle single-letter skills (C, R) with strict boundary
        - Support aliases/synonyms (e.g. 'postgres' -> 'PostgreSQL', 'golang' -> 'Go')
        """
        self.compiled_patterns = []
        self.skill_to_category = {}

        # 1. Map taxonomy skills to their categories
        for category, skills in self.taxonomy.items():
            for skill in skills:
                canonical = CANONICAL_ALIASES.get(skill.lower(), skill)
                self.skill_to_category[canonical] = category

        # 2. Collect all terms to compile: term -> (canonical, category)
        terms_to_compile: Dict[str, Tuple[str, str]] = {}

        for category, skills in self.taxonomy.items():
            for skill in skills:
                canonical = CANONICAL_ALIASES.get(skill.lower(), skill)
                terms_to_compile[skill] = (canonical, category)

        for alias, canonical in CANONICAL_ALIASES.items():
            category = self.skill_to_category.get(canonical, 'other')
            if alias not in terms_to_compile:
                terms_to_compile[alias] = (canonical, category)

        # 3. Sort terms by length descending
        sorted_terms = sorted(terms_to_compile.items(), key=lambda x: len(x[0]), reverse=True)

        for term, (canonical, category) in sorted_terms:
            lower_term = term.lower()
            if lower_term in ('c', 'r'):
                # Strict boundary for single-letter skills
                pattern = rf'(?i)(?:^|[\s,;/()|])({re.escape(term)})(?:$|[\s,;/()|])'
            elif any(char in term for char in ['+', '#', '.', '/', '-']):
                # For skills with symbols like C++, C#, .NET, Node.js, CI/CD
                pattern = rf'(?i)(?<![A-Za-z0-9])({re.escape(term)})(?![A-Za-z0-9])'
            else:
                # Standard word boundary for normal words
                pattern = rf'(?i)\b({re.escape(term)})\b'

            try:
                compiled = re.compile(pattern)
                self.compiled_patterns.append((compiled, canonical, category))
            except re.error:
                continue

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract unique canonical skills identified in the text.
        Returns a sorted list of unique skill names.
        """
        if not text:
            return []

        matched_skills: Set[str] = set()

        for pattern, canonical, _ in self.compiled_patterns:
            if pattern.search(text):
                matched_skills.add(canonical)

        return sorted(list(matched_skills), key=lambda s: s.lower())

    def extract_skills_by_category(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills grouped by their taxonomy category.
        """
        if not text:
            return {}

        results: Dict[str, Set[str]] = {}

        for pattern, canonical, category in self.compiled_patterns:
            if pattern.search(text):
                results.setdefault(category, set()).add(canonical)

        return {cat: sorted(list(skills), key=lambda s: s.lower()) for cat, skills in results.items()}

    def extract_skills_with_counts(self, text: str) -> Dict[str, int]:
        """
        Extract skills along with their frequency of occurrence in the text.
        """
        if not text:
            return {}

        frequencies: Dict[str, int] = {}

        for pattern, canonical, _ in self.compiled_patterns:
            matches = pattern.findall(text)
            if matches:
                count = len(matches)
                frequencies[canonical] = frequencies.get(canonical, 0) + count

        return dict(sorted(frequencies.items(), key=lambda item: item[1], reverse=True))


# Singleton default extractor instance for convenience
_default_extractor: Optional[SkillExtractor] = None

def get_skill_extractor() -> SkillExtractor:
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = SkillExtractor()
    return _default_extractor

def extract_skills(text: str) -> List[str]:
    return get_skill_extractor().extract_skills(text)
