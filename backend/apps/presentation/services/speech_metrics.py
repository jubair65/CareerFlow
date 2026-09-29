import re
from typing import Dict, Any, List, Tuple

# Standard filler words and hesitation phrases taxonomy
COMMON_FILLER_WORDS: List[str] = [
    "um",
    "uh",
    "er",
    "ah",
    "like",
    "you know",
    "basically",
    "actually",
    "literally",
    "sort of",
    "kind of",
    "i mean",
    "so yeah",
]

# Compile regular expressions with boundary assertions for accurate detection
_COMPILED_PATTERNS = [
    (phrase, re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE))
    for phrase in sorted(COMMON_FILLER_WORDS, key=len, reverse=True)
]


def count_words(text: str) -> int:
    """
    Returns the total word count in a text string.
    """
    if not text or not text.strip():
        return 0
    return len(text.strip().split())


def calculate_wpm(total_words: int, duration_seconds: float) -> float:
    """
    Calculates speaking pace in Words Per Minute (WPM) (US-12-T4).
    Formula: total_words / (duration_seconds / 60.0)

    Target optimal conversational/presentation pace: 130 - 160 WPM.
    """
    if duration_seconds <= 0 or total_words <= 0:
        return 0.0

    duration_minutes = duration_seconds / 60.0
    wpm = total_words / duration_minutes
    return round(wpm, 1)


def detect_filler_words(text: str) -> Dict[str, Any]:
    """
    Detects and counts filler words in the transcript using regex taxonomy (US-12-T5).

    Returns:
        Dict: {
            "filler_word_count": int,
            "filler_words_breakdown": Dict[str, int] # e.g. {"um": 4, "uh": 2, "like": 7}
        }
    """
    if not text or not text.strip():
        return {
            "filler_word_count": 0,
            "filler_words_breakdown": {}
        }

    breakdown: Dict[str, int] = {}
    total_count = 0

    # Search for multi-word and single-word fillers
    # To prevent duplicate counting when a phrase contains a smaller filler (e.g., 'so yeah' vs 'so'),
    # we work with a sanitized tracking string.
    tracking_text = text.lower()

    for phrase, pattern in _COMPILED_PATTERNS:
        matches = pattern.findall(tracking_text)
        count = len(matches)
        if count > 0:
            breakdown[phrase] = count
            total_count += count
            # Replace matched phrases with whitespace placeholder to prevent double-counting sub-words
            tracking_text = pattern.sub(" " * len(phrase), tracking_text)

    return {
        "filler_word_count": total_count,
        "filler_words_breakdown": breakdown
    }


def calculate_clarity_score(
    wpm: float,
    filler_count: int,
    total_words: int,
    duration_seconds: float
) -> int:
    """
    Calculates overall Speech Clarity Score (0 - 100) combining pace optimality
    and filler word frequency.

    - Optimal Pace (130 - 160 WPM): 50 points.
      Deducts 1 pt per WPM unit deviation from optimal boundaries [130, 160].
    - Filler Density: 50 points.
      Deducts points according to filler density per 100 words.
    """
    if total_words == 0 or duration_seconds <= 0:
        return 0

    # 1. Pace Score (0 - 50)
    if 130 <= wpm <= 160:
        pace_score = 50.0
    elif wpm < 130:
        pace_score = max(0.0, 50.0 - (130 - wpm))
    else:
        pace_score = max(0.0, 50.0 - (wpm - 160))

    # 2. Filler Score (0 - 50)
    # Normalized penalty based on filler word density
    filler_rate_per_100 = (filler_count / total_words) * 100 if total_words > 0 else 0
    filler_score = max(0.0, 50.0 - (filler_rate_per_100 * 5.0))

    total_score = int(round(pace_score + filler_score))
    return max(0, min(100, total_score))
