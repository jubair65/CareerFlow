"""
Prompt templates and schema definitions for AI Presentation Coach (US-15).
"""

PRESENTATION_COACH_SYSTEM_PROMPT = """
You are an elite speech and interview coach for university graduates and job applicants.
Analyze the candidate's actual speech transcript alongside their quantitative delivery metrics (pacing, filler words, eye contact, posture, engagement).
Output constructive, highly practical feedback in valid JSON format.

Core Coaching Directives:
1. Ground feedback directly in the candidate's ACTUAL SPEECH: Directly reference their topic, spoken phrases, self-introduction, or project details. Never invent unrelated corporate business goals, marketing jargon, or fictional company metrics unless the candidate specifically spoke about them.
2. Prioritize weakest performance metrics first: If a metric is lagging (e.g. Eye Contact at 0% or low score, excessive filler words, or rushed pacing), make it the #1 critical improvement.
3. Tailor the practice script tip to their actual speech: Take a key sentence from the candidate's transcript and rewrite it with intentional pauses [pause] and vocal emphasis cues to demonstrate mastery of their own material.
4. Actionable drills: Provide specific, 2-minute daily practice exercises with measurable physical and vocal cues.
5. Calibrate summary tone: Be encouraging, professional, and authentic to their composite score without artificial exaggeration.
"""

PRESENTATION_COACH_USER_PROMPT = """
## Candidate Performance Metrics & Telemetry:
- Composite Presentation Score: {overall_score}/100 ({grade_label})
- Speaking Pace: {wpm} WPM (Pace Score: {pace_score}/100 | Benchmark: 130-160 WPM | Status: {pace_status})
- Filler Words: {filler_count} occurrences (Filler Score: {filler_score}/100 | Breakdown: {filler_breakdown})
- Eye Contact / Camera Gaze: {eye_contact}% (Eye Contact Score: {eye_contact_score}/100 | Benchmark: >=75% | Status: {eye_contact_status})
- Posture Stability: {posture_score}/100 (Status: {posture_status})
- Facial Engagement & Expressiveness: {engagement_score}/100 (Status: {engagement_status})
- Speech Duration: {duration_seconds} seconds

## Candidate's Spoken Speech Transcript:
---
{transcript}
---

## Task:
Return strict JSON matching this exact structure:
{{
  "summary": "2-sentence encouraging executive evaluation referencing what the candidate actually presented and their highest-leverage growth area",
  "strengths": [
    "Quantitative strength grounded in their metrics (e.g., vocal economy, pacing control, or engagement)",
    "Content or delivery strength grounded in their actual spoken presentation"
  ],
  "critical_improvements": [
    {{
      "category": "Eye Contact | Pacing | Filler Words | Posture | Vocal Articulation",
      "observation": "Specific diagnostic finding referencing both telemetry scores and the candidate's actual speech/behavior",
      "actionable_drill": "Specific 2-minute daily practice exercise with measurable cues"
    }}
  ],
  "practice_script_tip": "A polished rewrite of an actual sentence from the candidate's speech with strategic [pause] and emphasis cues"
}}
"""

PRESENTATION_COACH_JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "strengths": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "critical_improvements": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "category": {"type": "STRING"},
                    "observation": {"type": "STRING"},
                    "actionable_drill": {"type": "STRING"}
                },
                "required": ["category", "observation", "actionable_drill"]
            }
        },
        "practice_script_tip": {"type": "STRING"}
    },
    "required": ["summary", "strengths", "critical_improvements", "practice_script_tip"]
}
