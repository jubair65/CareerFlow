"""
CV Extraction Service (US-07).
Unified extraction interface integrating text extraction, skill matching,
and education & experience parsing.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional

from .contracts import EducationItem, ExperienceItem, ExtractionResult
from .text_extractor import (
    clean_extracted_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text,
)
from .skill_extractor import (
    SkillExtractor,
    extract_skills,
    get_skill_extractor,
)
from .entity_extractor import (
    EntityExtractor,
    extract_education,
    extract_experience,
    extract_entities,
    get_entity_extractor,
    DEGREE_PATTERNS,
    INSTITUTION_KEYWORDS,
    KNOWN_INSTITUTIONS,
    TITLE_KEYWORDS,
)
from .pipeline import (
    CVExtractionPipeline,
    extract_cv_data,
    default_pipeline,
)

logger = logging.getLogger(__name__)

# Degree patterns matching: BSc, MSc, Bachelor, Master, BBA, MBA, Diploma, PhD
DEGREE_REGEX_PATTERNS = DEGREE_PATTERNS
YEAR_REGEX_PATTERN = r'\b(20\d{2}|19\d{2})\b|(\d+)\+?\s*(years?|yrs?)'


class CVExtractor(CVExtractionPipeline):
    """
    Unified CV Extractor class that orchestrates text extraction,
    skills identification, and entity extraction (education & experience).
    """
    pass


__all__ = [
    'CVExtractor',
    'CVExtractionPipeline',
    'default_pipeline',
    'extract_cv_data',
    'extract_text',
    'extract_text_from_pdf',
    'extract_text_from_docx',
    'clean_extracted_text',
    'SkillExtractor',
    'extract_skills',
    'get_skill_extractor',
    'EntityExtractor',
    'extract_education',
    'extract_experience',
    'extract_entities',
    'get_entity_extractor',
    'EducationItem',
    'ExperienceItem',
    'ExtractionResult',
    'DEGREE_REGEX_PATTERNS',
    'YEAR_REGEX_PATTERN',
]
