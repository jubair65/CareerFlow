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
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.api_key:
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
            try:
                from google.genai import types

                prompt = PRESENTATION_COACH_USER_PROMPT.format(**prepared_metrics)

                # Generate content with strict JSON mime-type
                response = client.models.generate_content(
                    model=self.model_name,
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
                    f"Gemini API presentation coaching invocation failed: {exc}. "
                    f"Falling back to rule-based diagnostics."
                )

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

        eye_contact = int(metrics.get('eye_contact') or metrics.get('eye_contact_score') or 75)
        posture_score = int(metrics.get('posture_score') or 80)
        engagement_score = int(metrics.get('engagement_score') or 75)
        overall_score = int(metrics.get('overall_score') or 78)

        return {
            "wpm": round(wpm, 1),
            "filler_count": filler_count,
            "filler_breakdown": breakdown_str,
            "eye_contact": eye_contact,
            "posture_score": posture_score,
            "engagement_score": engagement_score,
            "overall_score": overall_score,
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
        """
        wpm = metrics["wpm"]
        filler_count = metrics["filler_count"]
        eye_contact = metrics["eye_contact"]
        posture = metrics["posture_score"]
        engagement = metrics["engagement_score"]
        overall = metrics["overall_score"]

        strengths = []
        improvements = []

        # 1. Pacing Evaluation
        if 130 <= wpm <= 160:
            strengths.append(f"Optimal speaking pace at {wpm} WPM keeps your narrative crisp and engaging.")
        elif wpm < 130:
            improvements.append({
                "category": "Pacing",
                "observation": f"Speaking pace of {wpm} WPM is below the recommended 130-160 WPM interview cadence.",
                "actionable_drill": "The 60-Second Sprint: Read a 150-word industry paragraph aloud with a stopwatch, aiming to finish between 55 and 65 seconds."
            })
        else:
            improvements.append({
                "category": "Pacing",
                "observation": f"Speaking pace of {wpm} WPM is rushed (benchmark is 130-160 WPM), risking cognitive overload for the listener.",
                "actionable_drill": "The Comma-Breathe Drill: Read an elevator pitch aloud and enforce a deliberate 1-second silent breath at every comma and period."
            })

        # 2. Filler Words Evaluation
        if filler_count <= 2:
            strengths.append(f"Outstanding vocal economy with only {filler_count} filler words detected.")
        else:
            improvements.append({
                "category": "Filler Words",
                "observation": f"Detected {filler_count} filler occurrences ({metrics['filler_breakdown']}), reducing perceived authority.",
                "actionable_drill": "The Silent Pause Pivot: When formulating your next thought, keep your lips pressed together for 1 full second instead of vocalizing 'um' or 'like'."
            })

        # 3. Eye Contact Evaluation
        if eye_contact >= 75:
            strengths.append(f"Strong camera engagement with {eye_contact}% direct gaze adherence.")
        else:
            improvements.append({
                "category": "Eye Contact",
                "observation": f"Camera gaze maintained for {eye_contact}% of presentation (recommended >=75%).",
                "actionable_drill": "The Sticky Note Cue: Place a small bright sticker next to your webcam lens and maintain visual lock on the sticker during topic transitions."
            })

        # 4. Posture Alignment
        if posture >= 80:
            strengths.append(f"Solid posture stability ({posture}/100) projecting executive presence and confidence.")
        else:
            improvements.append({
                "category": "Posture",
                "observation": f"Posture stability measured at {posture}/100 with noticeable upper torso tilting or slouching.",
                "actionable_drill": "The Shoulder-Roll Reset: Prior to speaking, roll your shoulders back, place both feet flat on the floor, and keep the webcam at eye level."
            })

        # Ensure at least 2 strengths
        if len(strengths) < 2:
            if engagement >= 70:
                strengths.append(f"Warm facial expressiveness ({engagement}/100) establishes an authentic, approachable rapport.")
            else:
                strengths.append("Clear vocal articulation and structured narrative flow.")

        # Ensure at least 1 improvement
        if not improvements:
            improvements.append({
                "category": "Executive Polish",
                "observation": "Core presentation fundamentals are well established across vocal and physical metrics.",
                "actionable_drill": "Vocal Variety Drill: Emphasize the operative verbs in each sentence to add dynamic cadence to your executive pitch."
            })

        summary = (
            f"Overall presentation achieved an impressive {overall}/100 score. "
            f"Your key vocal and visual strengths are evident, and focusing on targeted drills will elevate your delivery to executive-level polish."
        )

        practice_tip = (
            "\"My key contribution was streamlining our data pipeline... [1-sec pause] "
            "...resulting in a 40% reduction in processing latency.\""
        )

        return {
            "summary": summary,
            "strengths": strengths,
            "critical_improvements": improvements,
            "practice_script_tip": practice_tip,
        }
