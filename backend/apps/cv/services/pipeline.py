import os
import logging
from typing import Optional, Callable, Dict, Any, List
from .contracts import ExtractionResult
from .text_extractor import extract_text
from .skill_extractor import get_skill_extractor, SkillExtractor

logger = logging.getLogger(__name__)


class CVExtractionPipeline:
    """
    Main pipeline orchestrator for CV data extraction (US-07).
    Coordinates:
    - Text extraction from PDF/DOCX (US-07-T2)
    - Technical and professional skills identification (US-07-T3)
    - Pluggable education and experience extraction (US-07-T4, implemented by Person 2)
    """

    def __init__(
        self,
        skill_extractor: Optional[SkillExtractor] = None,
        entity_extractor: Optional[Callable[[str], Dict[str, Any]]] = None,
    ):
        self.skill_extractor = skill_extractor or get_skill_extractor()
        # Pluggable hook for Person 2's entity extractor (Education & Experience)
        self.entity_extractor = entity_extractor

    def process_file(self, file_path: str, file_type: Optional[str] = None) -> ExtractionResult:
        """
        Execute full extraction pipeline on a file on disk.
        """
        if not os.path.exists(file_path):
            return ExtractionResult(
                raw_text="",
                success=False,
                error_message=f"File not found at: {file_path}"
            )

        try:
            # 1. US-07-T2: Text extraction & cleanup
            raw_text = extract_text(file_path, file_type=file_type)

            if not raw_text or not raw_text.strip():
                return ExtractionResult(
                    raw_text="",
                    word_count=0,
                    success=True,
                    error_message="Document appears to be empty or contains scanned images without extractable text."
                )

            words = raw_text.split()
            word_count = len(words)

            # 2. US-07-T3: Skills extraction
            skills = self.skill_extractor.extract_skills(raw_text)

            # 3. US-07-T4 (Teammate hook): Education & Experience extraction
            education: List[Dict[str, Any]] = []
            experience: List[Dict[str, Any]] = []

            if self.entity_extractor is not None:
                try:
                    entities = self.entity_extractor(raw_text)
                    education = entities.get('education', [])
                    experience = entities.get('experience', [])
                except Exception as ent_err:
                    logger.warning(f"Entity extractor warning: {ent_err}")

            return ExtractionResult(
                raw_text=raw_text,
                skills=skills,
                education=education,
                experience=experience,
                word_count=word_count,
                success=True,
            )

        except Exception as e:
            logger.error(f"Error in CV extraction pipeline: {str(e)}", exc_info=True)
            return ExtractionResult(
                raw_text="",
                success=False,
                error_message=str(e),
            )

    def process_candidate_cv(self, candidate_cv) -> ExtractionResult:
        """
        Process a CandidateCV Django model instance.
        """
        file_path = candidate_cv.file.path
        file_type = getattr(candidate_cv, 'file_type', None)
        return self.process_file(file_path, file_type=file_type)


# Default pipeline instance
default_pipeline = CVExtractionPipeline()


def extract_cv_data(file_path: str, file_type: Optional[str] = None) -> ExtractionResult:
    """Convenience functional interface to extract CV data."""
    return default_pipeline.process_file(file_path, file_type)
