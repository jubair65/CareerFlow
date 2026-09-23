import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from .contracts import EducationItem, ExperienceItem

logger = logging.getLogger(__name__)

# Degree recognition patterns
DEGREE_PATTERNS = [
    # Bachelor degrees
    (r'\b(?:b\.?sc\.?|bachelor(?:\'s)?(?:\s+of\s+science|\s+of\s+engineering|\s+of\s+arts|\s+of\s+business\s+administration)?|b\.?s\.?|b\.?e\.?|b\.?tech|b\.?a\.?)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'Bachelor'),
    # Master degrees
    (r'\b(?:m\.?sc\.?|master(?:\'s)?(?:\s+of\s+science|\s+of\s+engineering|\s+of\s+arts|\s+of\s+business\s+administration)?|m\.?s\.?|m\.?e\.?|m\.?tech|m\.?a\.?)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'Master'),
    # Business degrees
    (r'\b(?:bba|executive\s+bba)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'BBA'),
    (r'\b(?:mba|executive\s+mba|emba)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'MBA'),
    # Doctorate degrees
    (r'\b(?:ph\.?d\.?|doctor\s+of\s+philosophy|doctorate)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'PhD'),
    # Diplomas & secondary
    (r'\b(?:diploma|post\s+graduate\s+diploma|pgd)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'Diploma'),
    (r'\b(?:associate(?:\'s)?\s+degree|associate\s+of\s+science|associate\s+of\s+arts)\b(?:\s+(?:in|of)\s+[A-Za-z &,-]+)?', 'Associate Degree'),
    (r'\b(?:hsc|higher\s+secondary\s+certificate|ssc|secondary\s+school\s+certificate|a[- ]levels?|o[- ]levels?)\b', 'Secondary Education'),
]

# Keywords indicating educational institutions
INSTITUTION_KEYWORDS = [
    r'university',
    r'college',
    r'institute',
    r'school',
    r'academy',
    r'polytechnic',
    r'varsity',
]

# Well-known institution abbreviations / names
KNOWN_INSTITUTIONS = [
    'MIT', 'Stanford', 'Harvard', 'Oxford', 'Cambridge', 'UCLA', 'Berkeley',
    'BUET', 'DU', 'NSU', 'BRAC', 'IUB', 'AIUB', 'AUST', 'UIU', 'SUST', 'CUET', 'RUET', 'KUET',
]

# Common tech & professional job titles
TITLE_KEYWORDS = [
    r'software engineer(?:ing)?',
    r'software developer',
    r'frontend developer',
    r'frontend engineer',
    r'backend developer',
    r'backend engineer',
    r'full[- ]stack developer',
    r'full[- ]stack engineer',
    r'web developer',
    r'mobile developer',
    r'mobile application developer',
    r'devops engineer',
    r'cloud engineer',
    r'cloud architect',
    r'data scientist',
    r'data analyst',
    r'data engineer',
    r'machine learning engineer',
    r'ai engineer',
    r'qa engineer',
    r'quality assurance engineer',
    r'software quality assurance',
    r'test engineer',
    r'systems? architect',
    r'system administrator',
    r'database administrator',
    r'product manager',
    r'project manager',
    r'technical lead',
    r'tech lead',
    r'team lead',
    r'engineering manager',
    r'intern(?:ship)?',
    r'research assistant',
    r'graduate assistant',
    r'consultant',
    r'ui/ux designer',
    r'product designer',
]

# Section headers
EDUCATION_HEADERS = [
    'education',
    'educational background',
    'academic background',
    'academics',
    'academic qualifications',
    'qualifications',
]

EXPERIENCE_HEADERS = [
    'experience',
    'work experience',
    'professional experience',
    'employment history',
    'work history',
    'internship experience',
    'career history',
]

SECTION_BOUNDARY_HEADERS = [
    'skills', 'technical skills', 'skills & tools', 'projects', 'certifications',
    'awards', 'languages', 'interests', 'references', 'summary', 'about me', 'profile'
]


class EntityExtractor:
    """
    Extracts Education and Experience structured records from CV text (US-07-T4).
    """

    def __init__(self):
        self.year_pattern = re.compile(r'\b(19\d{2}|20\d{2})\b')
        self.year_range_pattern = re.compile(
            r'\b(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(19\d{2}|20\d{2}|present|current)\b',
            re.IGNORECASE
        )
        self.duration_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)',
            re.IGNORECASE
        )
        self.gpa_pattern = re.compile(
            r'\b(?:gpa|cgpa|grade)[:\s]*([0-4](?:\.\d{1,2})?|[0-5](?:\.\d{1,2})?)(?:\s*/\s*[45](?:\.0)?)?\b',
            re.IGNORECASE
        )

    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Segment the CV text into identifiable sections based on standard headings.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sections: Dict[str, List[str]] = {
            'education': [],
            'experience': [],
            'other': [],
        }

        current_section = 'other'

        for line in lines:
            line_lower = line.lower().strip(':').strip('-').strip()
            
            # Check for education header
            if any(line_lower == h or line_lower.startswith(f"{h}:") for h in EDUCATION_HEADERS):
                current_section = 'education'
                continue
            
            # Check for experience header
            if any(line_lower == h or line_lower.startswith(f"{h}:") for h in EXPERIENCE_HEADERS):
                current_section = 'experience'
                continue

            # Check for another known header that ends current section
            if any(line_lower == h or line_lower.startswith(f"{h}:") for h in SECTION_BOUNDARY_HEADERS):
                current_section = 'other'
                continue

            sections[current_section].append(line)

        return {
            'education': '\n'.join(sections['education']),
            'experience': '\n'.join(sections['experience']),
            'other': '\n'.join(sections['other']),
        }

    def _extract_year_or_range(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Extract year or year range and compute duration in years.
        """
        range_match = self.year_range_pattern.search(text)
        if range_match:
            start_yr = int(range_match.group(1))
            end_val = range_match.group(2).lower()
            if end_val in ('present', 'current'):
                # Current year is 2026 as per system metadata
                end_yr = 2026
            else:
                end_yr = int(end_val)
            duration_years = max(0.5, float(end_yr - start_yr))
            return range_match.group(0), duration_years

        dur_match = self.duration_pattern.search(text)
        if dur_match:
            try:
                years = float(dur_match.group(1))
                return dur_match.group(0), years
            except ValueError:
                pass

        yr_match = self.year_pattern.search(text)
        if yr_match:
            return yr_match.group(1), 1.0

        return None, 0.0

    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract structured education entries from CV text.
        Returns list of dicts with: degree, institution, year, grade.
        """
        if not text or not text.strip():
            return []

        sections = self.extract_sections(text)
        edu_section = sections.get('education', '')
        
        # We search both the education section first, or fallback to the whole text
        search_blocks = [edu_section] if edu_section else []
        search_blocks.append(text)

        found_items: List[Dict[str, Any]] = []
        seen_combinations = set()

        for block in search_blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            for idx, line in enumerate(lines):
                detected_degree = None
                detected_degree_canonical = None

                for pattern, canonical in DEGREE_PATTERNS:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        detected_degree = match.group(0).strip()
                        detected_degree_canonical = canonical
                        break

                if not detected_degree:
                    continue

                # Look for institution on the same line or adjacent lines (up to 2 before/after)
                context_lines = []
                start_i = max(0, idx - 1)
                end_i = min(len(lines), idx + 3)
                for ci in range(start_i, end_i):
                    context_lines.append(lines[ci])
                combined_context = ' | '.join(context_lines)

                # Search institution
                detected_inst = ""
                # Look for known institutions first
                for known in KNOWN_INSTITUTIONS:
                    if re.search(r'\b' + re.escape(known) + r'(?:\s+University|\s+Institute)?\b', combined_context, re.IGNORECASE):
                        detected_inst = known
                        break

                if not detected_inst:
                    # Look for institution keyword pattern (e.g. Stanford University, Dhaka College)
                    for kw in INSTITUTION_KEYWORDS:
                        inst_match = re.search(
                            r'([A-Z][A-Za-z0-9&.\'\- ]*?\s+' + kw + r'(?:\s+of\s+[A-Za-z0-9&.\'\- ]+)?)',
                            combined_context,
                            re.IGNORECASE
                        )
                        if inst_match:
                            candidate_inst = inst_match.group(1).strip()
                            # Strip out the degree if accidentally included
                            if detected_degree and detected_degree in candidate_inst:
                                candidate_inst = candidate_inst.replace(detected_degree, '').strip(' -|,')
                            if len(candidate_inst) > 3:
                                detected_inst = candidate_inst
                                break

                # Search year and grade in the context
                year_str, _ = self._extract_year_or_range(combined_context)
                
                grade_match = self.gpa_pattern.search(combined_context)
                grade_str = grade_match.group(0) if grade_match else None

                combo_key = (detected_degree_canonical, detected_inst or 'Unknown', year_str)
                if combo_key not in seen_combinations:
                    seen_combinations.add(combo_key)
                    item = EducationItem(
                        degree=detected_degree,
                        institution=detected_inst or "Not Specified",
                        year=year_str,
                        grade=grade_str
                    )
                    found_items.append(item.to_dict())

            if found_items:
                # If we found items in the dedicated education section, we don't need the fallback
                break

        return found_items

    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract structured work experience entries from CV text.
        Returns list of dicts with: title, company, duration, duration_years, years_count, description.
        """
        if not text or not text.strip():
            return []

        sections = self.extract_sections(text)
        exp_section = sections.get('experience', '')
        
        search_blocks = [exp_section] if exp_section else []
        search_blocks.append(text)

        found_items: List[Dict[str, Any]] = []
        seen_titles = set()

        for block in search_blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            for idx, line in enumerate(lines):
                detected_title = None

                for kw in TITLE_KEYWORDS:
                    title_match = re.search(
                        r'\b(?:senior|junior|lead|principal|staff|associate|intern)?\s*' + kw + r'\b',
                        line,
                        re.IGNORECASE
                    )
                    if title_match:
                        detected_title = title_match.group(0).strip().title()
                        break

                if not detected_title:
                    continue

                # Context around this line
                start_i = max(0, idx - 1)
                end_i = min(len(lines), idx + 3)
                context_lines = lines[start_i:end_i]
                combined_context = ' | '.join(context_lines)

                # Extract company
                company = ""
                # Check for "at <Company>" or "@ <Company>" on the title line first
                line_comp = re.search(r'(?:at|@)\s+([A-Za-z0-9&.\'\-]+(?:\s+[A-Za-z0-9&.\'\-]+)*)', line)
                if line_comp:
                    company = line_comp.group(1).strip(' -|,')
                else:
                    # Check for delimiter on same line: e.g. "Software Engineer | Acme Corp" or "Software Engineer - Google"
                    split_parts = re.split(r'\s+[|–\-]\s+', line)
                    if len(split_parts) >= 2:
                        for part in split_parts:
                            part_clean = part.strip()
                            if part_clean.lower() != detected_title.lower() and not self.year_pattern.search(part_clean) and len(part_clean) > 2:
                                company = part_clean
                                break

                # Fallback to context around line
                if not company:
                    comp_match = re.search(
                        r'(?:at|@)\s+([A-Za-z0-9&.\'\-]+(?:\s+[A-Za-z0-9&.\'\-]+)*)',
                        combined_context
                    )
                    if comp_match:
                        company = comp_match.group(1).strip(' -|,')

                # Duration & years count
                dur_str, dur_years = self._extract_year_or_range(combined_context)

                title_key = (detected_title.lower(), (company or 'Unknown').lower(), dur_str)
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    item = ExperienceItem(
                        title=detected_title,
                        company=company or "Not Specified",
                        duration=dur_str,
                        years_count=dur_years,
                        description=""
                    )
                    d = item.to_dict()
                    # Also include duration_years for database model schema compatibility
                    d['duration_years'] = dur_years
                    found_items.append(d)

            if found_items:
                break

        return found_items

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract both education and experience in a single call.
        """
        return {
            'education': self.extract_education(text),
            'experience': self.extract_experience(text),
        }


# Global extractor instance
_default_entity_extractor: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    global _default_entity_extractor
    if _default_entity_extractor is None:
        _default_entity_extractor = EntityExtractor()
    return _default_entity_extractor


def extract_education(text: str) -> List[Dict[str, Any]]:
    return get_entity_extractor().extract_education(text)


def extract_experience(text: str) -> List[Dict[str, Any]]:
    return get_entity_extractor().extract_experience(text)


def extract_entities(text: str) -> Dict[str, Any]:
    return get_entity_extractor().extract_all(text)
