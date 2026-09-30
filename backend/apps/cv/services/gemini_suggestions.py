"""
Gemini AI-powered CV suggestion generator (Hybrid approach).

Strategy:
- The rule-based scorer (scorer.py) still computes all numeric scores — fast, deterministic.
- This module calls Gemini to generate the 3 *primary* suggestions with full CV context.
- The regex engine's suggestions are used as structured context/hints to guide Gemini.
- Falls back to the rule-based suggestions if Gemini is unavailable or the API key is not set.

This gives us the best of both worlds:
  ✅ Deterministic, auditable scores (regex)
  ✅ Contextual, human-sounding suggestions that cite the actual CV (Gemini)
"""

import os
import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded Gemini client (only created once successfully)
_gemini_client = None

# Preferred order of Gemini models for maximum reliability and uptime:
# 1. gemini-3.5-flash-lite: Fastest, highly available, no 503 capacity spikes
# 2. gemini-3.5-flash: High reasoning, highly capable
# 3. gemini-3.1-flash-lite: Dependable fallback
# 4. gemini-3-flash-preview: Preview generation
# 5. gemini-3.8-flash: Latest flagship flash
DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
]


def _get_gemini_client():
    """
    Lazily initialise the Gemini client.
    Re-checks the env var every call so it works even if the key
    was added to .env after the module was first imported.
    Returns None (silently) if key is not configured.
    """
    global _gemini_client

    if _gemini_client is not None:
        return _gemini_client

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    # If not in os.environ yet, try loading backend/.env
    if not api_key:
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            else:
                load_dotenv()
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        except Exception:
            pass

    if not api_key or api_key == "your-gemini-api-key-here":
        # Key not set yet — silent, no log spam
        return None

    try:
        from google import genai  # google-genai SDK
        client = genai.Client(api_key=api_key)
        _gemini_client = client
        logger.info("Gemini client initialised successfully.")
        return _gemini_client
    except Exception as exc:
        logger.warning(
            "Failed to initialise Gemini client: %s — will use rule-based suggestions.",
            exc,
        )
        return None


def _build_prompt(
    raw_text: str,
    overall_score: int,
    formatting_score: int,
    keyword_score: int,
    clarity_score: int,
    experience_score: int,
    education_score: int,
    skills: List[str],
    weak_phrases: List[str],
    weak_bullets: List[str],
    rule_based_hints: List[str],
    role_profile: Optional[str],
) -> str:
    """Build the structured prompt for Gemini."""

    # Truncate CV text to stay within a reasonable token budget (~2000 chars)
    cv_excerpt = raw_text.strip()[:2200] if raw_text else "(no text extracted)"
    if len(raw_text.strip()) > 2200:
        cv_excerpt += "\n[...truncated for brevity...]"

    skills_str = ", ".join(skills[:20]) if skills else "None detected"
    weak_phrases_str = ", ".join(f'"{p}"' for p in weak_phrases[:5]) if weak_phrases else "None"
    weak_bullets_str = "\n".join(f'  - "{b}"' for b in weak_bullets[:3]) if weak_bullets else "  None"
    hints_str = "\n".join(f"  {i+1}. {h}" for i, h in enumerate(rule_based_hints[:6]))
    role_str = role_profile.replace("_", " ").title() if role_profile else "Not detected"

    return f"""You are an expert CV/resume coach reviewing a candidate's CV for ATS compliance and recruiter impact.

## CV Analysis Data
- **Overall Score**: {overall_score}/100
- **Formatting Score**: {formatting_score}/100 (weight: 20%)
- **Keyword Strength Score**: {keyword_score}/100 (weight: 30%)
- **Clarity & Metrics Score**: {clarity_score}/100 (weight: 30%)
- **Experience Score**: {experience_score}/100 (weight: 10%)
- **Education Score**: {education_score}/100 (weight: 10%)
- **Detected Role Profile**: {role_str}
- **Detected Skills**: {skills_str}
- **Weak Passive Phrases Found**: {weak_phrases_str}
- **Bullet Points Lacking Metrics**:
{weak_bullets_str}

## Rule-Based Signal Hints (use as context, do NOT copy verbatim)
{hints_str}

## CV Text Excerpt
---
{cv_excerpt}
---

## Your Task
Write exactly **3 specific, high-impact CV improvement suggestions** for this candidate.

**Requirements:**
1. Each suggestion must be directly grounded in the CV text above — reference actual phrases, bullet points, skills, or sections you can see.
2. Write in second person ("Your bullet...", "You mention...", "In your Experience section...").
3. Be specific and practical — tell the candidate *exactly what to change* and *why*, not just general advice.
4. Where the CV has weak bullets (no numbers), quote the weak bullet and show a concrete rewrite example with metrics.
5. Address the biggest weaknesses first (lowest scoring dimensions).
6. Keep each suggestion to 2-4 sentences maximum.
7. Do NOT include numbering, bullet points, or headers in your response — output ONLY the 3 suggestions separated by a blank line.
8. Do NOT mention the word "ATS" more than once across all 3 suggestions.
9. Do NOT repeat the same suggestion or say the same thing twice.

Respond with exactly 3 paragraphs, each being one actionable suggestion. Nothing else.
"""


def _parse_gemini_response(text: str) -> List[str]:
    """
    Parse Gemini's response into a clean list of up to 3 suggestions.
    Handles numbered lists, blank-line separated paragraphs, and mixed formats.
    """
    if not text:
        return []

    # Remove markdown headers/bold
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Split on blank lines (paragraph-separated)
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]

    # If still looks like a numbered list, split on number-dot pattern
    if len(paragraphs) <= 2:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        numbered = []
        current = []
        for line in lines:
            if re.match(r'^\d+[\.\)]\s+', line):
                if current:
                    numbered.append(' '.join(current))
                current = [re.sub(r'^\d+[\.\)]\s+', '', line)]
            else:
                current.append(line)
        if current:
            numbered.append(' '.join(current))
        if len(numbered) > len(paragraphs):
            paragraphs = numbered

    # Clean and deduplicate
    seen = set()
    cleaned = []
    for p in paragraphs:
        p = p.strip().strip('-•*').strip()
        # Strip leading "N." or "N)" numbering
        p = re.sub(r'^\d+[\.\)]\s*', '', p)
        if len(p) > 20 and p not in seen:
            seen.add(p)
            cleaned.append(p)
        if len(cleaned) == 3:
            break

    return cleaned


def generate_gemini_suggestions(
    raw_text: str,
    overall_score: int,
    formatting_score: int,
    keyword_score: int,
    clarity_score: int,
    experience_score: int,
    education_score: int,
    skills: List[str],
    weak_phrases: List[str],
    weak_bullets: List[str],
    rule_based_hints: List[str],
    role_profile: Optional[str] = None,
) -> Optional[List[str]]:
    """
    Call Gemini to generate CV-specific suggestions.

    Returns a list of up to 6 suggestion strings, or None if:
    - Gemini API key is not configured
    - The API call fails for any reason (caller should fall back to rule-based)
    """
    client = _get_gemini_client()
    if client is None:
        print("[Gemini] No client — falling back to rule-based.")
        return None

    prompt = _build_prompt(
        raw_text=raw_text,
        overall_score=overall_score,
        formatting_score=formatting_score,
        keyword_score=keyword_score,
        clarity_score=clarity_score,
        experience_score=experience_score,
        education_score=education_score,
        skills=skills,
        weak_phrases=weak_phrases,
        weak_bullets=weak_bullets,
        rule_based_hints=rule_based_hints,
        role_profile=role_profile,
    )

    models_to_try = []
    user_configured_model = os.environ.get("GEMINI_MODEL", "").strip()
    if user_configured_model:
        models_to_try.append(user_configured_model)
    for m in DEFAULT_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    for model_name in models_to_try:
        try:
            print(f"[Gemini] Calling {model_name} for CV suggestions...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            raw_response = response.text or ""
            suggestions = _parse_gemini_response(raw_response)
            print(f"[Gemini] {model_name} returned {len(suggestions)} parsed suggestions.")

            if len(suggestions) >= 2:
                print(f"[Gemini] SUCCESS with {model_name} — using AI suggestions.")
                logger.info("Gemini (%s) generated %d CV suggestions successfully.", model_name, len(suggestions))
                return suggestions[:3]
            else:
                print(f"[Gemini] {model_name} returned too few suggestions ({len(suggestions)}), trying next candidate...")
        except Exception as exc:
            print(f"[Gemini] {model_name} call failed: {exc}")
            logger.warning("Gemini model %s failed: %s. Trying fallback model.", model_name, exc)
            continue

    print("[Gemini] All Gemini candidate models failed — falling back to rule-based.")
    logger.warning("All Gemini candidate models failed. Using rule-based fallback.")
    return None

