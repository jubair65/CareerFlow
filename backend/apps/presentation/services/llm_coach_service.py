"""
Dedicated Gemini Presentation Coach Service (US-15-T2, US-15-T3).
Integrates Google Gemini API to produce structured, constructive, actionable
presentation feedback from quantitative speech and behavioral metrics.
"""

import os
import json
import logging
from typing import Dict, Any, List

from .llm_prompts import (
    PRESENTATION_COACH_SYSTEM_PROMPT,
    PRESENTATION_COACH_USER_PROMPT,
)

logger = logging.getLogger(__name__)


class GeminiPresentationCoachService:
    """
    Service layer wrapping Google Gemini API for candidate presentation coaching.
    Enforces structured JSON output and provides deterministic fallback logic.
    """

    def __init__(self, api_key: str = None, model: str = None):
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                try:
                    from dotenv import load_dotenv
                    from pathlib import Path
                    env_file = Path(__file__).resolve().parent.parent.parent.parent / '.env'
                    if env_file.exists():
                        load_dotenv(env_file)
                    else:
                        load_dotenv()
                    api_key = os.getenv('GEMINI_API_KEY')
                except Exception:
                    pass
        self.api_key = api_key
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.api_key or self.api_key == "your-gemini-api-key-here":
            logger.warning("GEMINI_API_KEY is not set. Service will fall back to rule-based coaching.")
            return None

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            return self._client
        except Exception as e:
            logger.error(f"Failed to initialize google.genai client: {e}")
            return None

    def generate_feedback(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized presentation suggestions using Gemini API.
        Falls back to rule-based diagnostic suggestions if the API call is unavailable or fails.
        """
        prepared_metrics = self._normalize_metrics(metrics)

        client = self._get_client()
        if client is not None:
            from google.genai import types

            prompt = PRESENTATION_COACH_USER_PROMPT.format(**prepared_metrics)

            candidate_models = []
            if self.model_name:
                candidate_models.append(self.model_name)
            for m in ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-3.8-flash']:
                if m not in candidate_models:
                    candidate_models.append(m)

            for model_id in candidate_models:
                try:
                    # Generate content with strict JSON mime-type
                    response = client.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=PRESENTATION_COACH_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                            temperature=0.3,
                        ),
                    )

                    raw_text = getattr(response, 'text', '') or ''
                    parsed = self.validate_and_sanitize_feedback(raw_text, prepared_metrics)
                    if parsed:
                        return parsed
                except Exception as exc:
                    logger.warning(
                        f"Gemini model {model_id} invocation failed: {exc}. Trying fallback..."
                    )
                    continue

        return self.generate_rule_based_fallback(prepared_metrics)

    def _normalize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and ensure safe defaults for all prompt interpolation keys."""
        wpm = float(metrics.get('wpm') or metrics.get('words_per_minute') or 140.0)
        filler_count = int(metrics.get('filler_count') or metrics.get('filler_word_count') or 0)
        filler_breakdown = metrics.get('filler_breakdown') or metrics.get('filler_words_breakdown') or {}
        if isinstance(filler_breakdown, dict):
            breakdown_str = ", ".join(f"{k}: {v}" for k, v in filler_breakdown.items()) if filler_breakdown else "none detected"
        else:
            breakdown_str = str(filler_breakdown)

        eye_contact = int(metrics.get('eye_contact') if metrics.get('eye_contact') is not None else (metrics.get('eye_contact_score') or 75))
        posture_score = int(metrics.get('posture_score') or 80)
        engagement_score = int(metrics.get('engagement_score') or 75)
        overall_score = int(metrics.get('overall_score') or 78)
        pace_score = int(metrics.get('pace_score') or 80)
        filler_score = int(metrics.get('filler_score') or 85)
        eye_contact_score = int(metrics.get('eye_contact_score') if metrics.get('eye_contact_score') is not None else eye_contact)
        duration_seconds = round(float(metrics.get('duration_seconds') or 0.0), 1)

        raw_transcript = str(metrics.get('transcript') or '').strip()
        transcript = raw_transcript if raw_transcript else "(No spoken words detected in this recording)"

        # Pacing status
        if wpm == 0:
            pace_status = "Silent / No Speech Detected"
        elif 130 <= wpm <= 160:
            pace_status = f"Optimal interview cadence ({round(wpm, 1)} WPM)"
        elif wpm < 130:
            pace_status = f"Deliberate / below 130-160 WPM target ({round(wpm, 1)} WPM)"
        else:
            pace_status = f"Fast / Rushed ({round(wpm, 1)} WPM vs 130-160 WPM target)"

        # Eye contact status
        if eye_contact == 0:
            eye_contact_status = "CRITICAL DEFICIT (0% - looking down, away, or reading from screen)"
        elif eye_contact < 60:
            eye_contact_status = f"Needs significant improvement ({eye_contact}% vs >=75% target)"
        elif eye_contact < 75:
            eye_contact_status = f"Acceptable ({eye_contact}% vs >=75% target)"
        else:
            eye_contact_status = f"Strong camera gaze adherence ({eye_contact}%)"

        # Posture status
        if posture_score < 60:
            posture_status = "Noticeable slouching, head tilt, or fidgeting"
        elif posture_score < 75:
            posture_status = "Moderate alignment; slight upper body tilt"
        else:
            posture_status = "Solid upright posture"

        # Engagement status
        if engagement_score < 60:
            engagement_status = "Low facial expressiveness"
        elif engagement_score < 75:
            engagement_status = "Moderate facial expressiveness"
        else:
            engagement_status = "Warm, attentive expressiveness"

        # Grade label
        if overall_score >= 85:
            grade_label = "Excellent"
        elif overall_score >= 70:
            grade_label = "Competent"
        else:
            grade_label = "Needs Practice"

        return {
            "wpm": round(wpm, 1),
            "filler_count": filler_count,
            "filler_breakdown": breakdown_str,
            "eye_contact": eye_contact,
            "eye_contact_score": eye_contact_score,
            "eye_contact_status": eye_contact_status,
            "posture_score": posture_score,
            "posture_status": posture_status,
            "engagement_score": engagement_score,
            "engagement_status": engagement_status,
            "overall_score": overall_score,
            "pace_score": pace_score,
            "pace_status": pace_status,
            "filler_score": filler_score,
            "grade_label": grade_label,
            "duration_seconds": duration_seconds,
            "transcript": transcript,
            "raw_transcript": raw_transcript,
        }

    def validate_and_sanitize_feedback(self, raw_input: Any, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        US-15-T3: Parses raw JSON (stripping markdown codeblocks if necessary)
        and verifies that all required coaching fields exist and meet schema constraints.
        """
        if isinstance(raw_input, str):
            clean_str = raw_input.strip()
            # Strip markdown code blocks
            if clean_str.startswith("```"):
                lines = clean_str.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_str = "\n".join(lines).strip()

            try:
                data = json.loads(clean_str)
            except json.JSONDecodeError as err:
                logger.error(f"JSON decode failure in Gemini feedback: {err}")
                return None
        elif isinstance(raw_input, dict):
            data = raw_input
        else:
            return None

        # Schema validation
        if not isinstance(data.get("summary"), str) or not data["summary"].strip():
            return None

        strengths = data.get("strengths")
        if not isinstance(strengths, list) or len(strengths) == 0:
            return None

        improvements = data.get("critical_improvements")
        if not isinstance(improvements, list) or len(improvements) == 0:
            return None

        sanitized_improvements = []
        for item in improvements:
            if not isinstance(item, dict):
                continue
            cat = str(item.get("category", "General Polish")).strip()
            obs = str(item.get("observation", "")).strip()
            drill = str(item.get("actionable_drill", "")).strip()
            if obs and drill:
                sanitized_improvements.append({
                    "category": cat,
                    "observation": obs,
                    "actionable_drill": drill,
                })

        if not sanitized_improvements:
            return None

        practice_tip = str(data.get("practice_script_tip") or "").strip()
        if not practice_tip:
            practice_tip = "Pause... breathe... then deliver your core point with deliberate inflection."

        return {
            "summary": data["summary"].strip(),
            "strengths": [str(s).strip() for s in strengths if str(s).strip()],
            "critical_improvements": sanitized_improvements,
            "practice_script_tip": practice_tip,
        }

    def generate_rule_based_fallback(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        High-fidelity diagnostic rule engine providing constructive feedback
        when LLM API is unavailable, offline, or experiencing rate limits.
        Prioritizes the candidate's actual lowest scores and speech content.
        """
        wpm = metrics["wpm"]
        filler_count = metrics["filler_count"]
        eye_contact = metrics["eye_contact"]
        posture = metrics["posture_score"]
        engagement = metrics["engagement_score"]
        overall = metrics["overall_score"]
        raw_transcript = metrics.get("raw_transcript", "")

        strengths = []
        improvement_candidates = []

        # 1. Pacing Evaluation
        if 130 <= wpm <= 160:
            strengths.append(f"Optimal speaking pace at {wpm} WPM keeps your narrative crisp and engaging.")
        elif wpm < 130:
            severity = 130 - wpm
            obs = (
                f"Speaking pace of {wpm} WPM is below the recommended 130-160 WPM interview cadence."
                if wpm > 0 else "No speech audio detected in this recording."
            )
            improvement_candidates.append((
                severity,
                {
                    "category": "Pacing",
                    "observation": obs,
                    "actionable_drill": "The 60-Second Sprint: Read a 150-word industry paragraph aloud with a stopwatch, aiming to finish between 55 and 65 seconds."
                }
            ))
        else:
            severity = wpm - 160
            improvement_candidates.append((
                severity,
                {
                    "category": "Pacing",
                    "observation": f"Speaking pace of {wpm} WPM is rushed (benchmark is 130-160 WPM), risking cognitive overload for the listener.",
                    "actionable_drill": "The Comma-Breathe Drill: Read an elevator pitch aloud and enforce a deliberate 1-second silent breath at every comma and period."
                }
            ))

        # 2. Filler Words Evaluation
        if filler_count <= 2 and wpm > 0:
            strengths.append(f"Outstanding vocal economy with only {filler_count} filler words detected.")
        elif filler_count > 2:
            severity = filler_count * 8
            improvement_candidates.append((
                severity,
                {
                    "category": "Filler Words",
                    "observation": f"Detected {filler_count} filler occurrences ({metrics['filler_breakdown']}), reducing perceived authority.",
                    "actionable_drill": "The Silent Pause Pivot: When formulating your next thought, keep your lips pressed together for 1 full second instead of vocalizing 'um' or 'like'."
                }
            ))

        # 3. Eye Contact Evaluation
        if eye_contact >= 75:
            strengths.append(f"Strong camera engagement with {eye_contact}% direct gaze adherence.")
        else:
            # 0% eye contact is a critical issue -> high priority
            severity = (75 - eye_contact) * 1.5
            obs = (
                "Camera gaze was 0% — you were looking down or reading from your screen instead of the webcam lens."
                if eye_contact == 0
                else f"Camera gaze maintained for {eye_contact}% of presentation (recommended >=75%)."
            )
            improvement_candidates.append((
                severity,
                {
                    "category": "Eye Contact",
                    "observation": obs,
                    "actionable_drill": "The Sticky Note Cue: Place a small bright sticker directly next to your webcam lens and maintain visual lock on the sticker during topic transitions."
                }
            ))

        # 4. Posture Alignment
        if posture >= 80:
            strengths.append(f"Solid posture stability ({posture}/100) projecting executive presence and confidence.")
        else:
            severity = (80 - posture)
            improvement_candidates.append((
                severity,
                {
                    "category": "Posture",
                    "observation": f"Posture stability measured at {posture}/100 with noticeable upper torso tilting or slouching.",
                    "actionable_drill": "The Shoulder-Roll Reset: Prior to speaking, roll your shoulders back, place both feet flat on the floor, and keep the webcam at eye level."
                }
            ))

        # Sort improvements by severity descending (highest deficit first)
        improvement_candidates.sort(key=lambda x: x[0], reverse=True)
        improvements = [item[1] for item in improvement_candidates]

        # Ensure at least 2 strengths
        if len(strengths) < 2:
            if engagement >= 70:
                strengths.append(f"Warm facial expressiveness ({engagement}/100) establishes an authentic, approachable rapport.")
            else:
                strengths.append("Clear narrative structure and professional tone throughout.")

        # Ensure at least 1 improvement
        if not improvements:
            improvements.append({
                "category": "Executive Polish",
                "observation": "Core presentation fundamentals are well established across vocal and physical metrics.",
                "actionable_drill": "Vocal Variety Drill: Emphasize the operative verbs in each sentence to add dynamic cadence to your executive pitch."
            })

        # Summary calibrated to score
        if overall >= 85:
            summary = (
                f"Outstanding presentation scored at {overall}/100 (Excellent). "
                f"Your delivery commands strong executive presence with polished pacing and poise."
            )
        elif overall >= 70:
            summary = (
                f"Solid presentation baseline scoring {overall}/100 (Competent). "
                f"Your core message is clear, and addressing your primary delivery focal area will rapidly elevate your recruiter impact."
            )
        else:
            summary = (
                f"Presentation scored {overall}/100 (Needs Practice). "
                f"Focusing on direct camera eye contact and vocal delivery fundamentals will significantly boost your interview confidence."
            )

        # Grounded practice tip from actual transcript if available
        if raw_transcript:
            import re
            sentences = [s.strip() for s in re.split(r'[.!?]', raw_transcript) if len(s.strip()) > 15]
            if sentences:
                first_sent = sentences[0]
                if ',' in first_sent:
                    parts = first_sent.split(',', 1)
                    practice_tip = f"\"{parts[0].strip()}... [1-sec pause] {parts[1].strip()}.\""
                else:
                    words = first_sent.split()
                    mid = max(1, len(words) // 2)
                    practice_tip = f"\"{' '.join(words[:mid])}... [1-sec pause] {' '.join(words[mid:])}.\""
            else:
                practice_tip = "\"Good morning... [1-sec pause] My name is [Name], and I look forward to discussing our work.\""
        else:
            practice_tip = "\"Good morning... [1-sec pause] My name is [Name], and I look forward to discussing our work.\""

        return {
            "summary": summary,
            "strengths": strengths,
            "critical_improvements": improvements[:3],
            "practice_script_tip": practice_tip,
        }
