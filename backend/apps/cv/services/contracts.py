from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class EducationItem:
    degree: str
    institution: str
    year: Optional[str] = None
    grade: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'degree': self.degree,
            'institution': self.institution,
            'year': self.year,
            'grade': self.grade,
        }


@dataclass
class ExperienceItem:
    title: str
    company: str
    duration: Optional[str] = None
    years_count: Optional[float] = 0.0
    description: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'company': self.company,
            'duration': self.duration,
            'years_count': self.years_count,
            'description': self.description,
        }


@dataclass
class ExtractionResult:
    raw_text: str
    skills: List[str] = field(default_factory=list)
    education: List[Dict[str, Any]] = field(default_factory=list)
    experience: List[Dict[str, Any]] = field(default_factory=list)
    word_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    is_scanned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_text': self.raw_text,
            'skills': self.skills,
            'education': self.education,
            'experience': self.experience,
            'word_count': self.word_count,
            'success': self.success,
            'error_message': self.error_message,
            'is_scanned': self.is_scanned,
        }
