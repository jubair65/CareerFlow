"""
Prompt templates and schema definitions for AI Presentation Coach (US-15).
"""

PRESENTATION_COACH_SYSTEM_PROMPT = """
You are an elite executive speech and interview coach for university graduates and job applicants.
Analyze the quantitative presentation metrics provided and output constructive, highly actionable feedback in valid JSON format.
Always provide specific, 2-minute daily practice drills rather than vague general advice.
Your tone is professional, encouraging, and razor-focused on measurable improvement.
"""

PRESENTATION_COACH_USER_PROMPT = """
Candidate Performance Metrics:
- Speaking Speed: {wpm} WPM (Target: 130-160 WPM)
- Filler Words Count: {filler_count} occurrences (Top fillers: {filler_breakdown})
- Eye Contact: {eye_contact}% of presentation duration looking directly at camera
- Posture Stability Score: {posture_score}/100
- Facial Engagement Score: {engagement_score}/100
- Composite Presentation Score: {overall_score}/100

Return strict JSON matching this exact structure:
{{
  "summary": "2-sentence encouraging executive evaluation highlighting key impact and focus area",
  "strengths": [
    "Clear quantitative strength 1",
    "Clear behavioral or vocal strength 2"
  ],
  "critical_improvements": [
    {{
      "category": "Pacing | Eye Contact | Posture | Filler Words",
      "observation": "Specific quantitative finding from the performance metrics",
      "actionable_drill": "Specific 2-minute daily practice exercise with measurable cues"
    }}
  ],
  "practice_script_tip": "A sample sentence demonstrating intentional pacing, phrasing, and silent pause"
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
