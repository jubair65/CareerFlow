# Sprint 3 UI Testing Report — Task US-15-T6

**Sprint:** Sprint 3 (Presentation AI)  
**User Story:** US-15: AI Improvement Suggestions  
**Task:** US-15-T6 (UI Testing for AI Improvement Suggestions & Drills Display)  
**Tester / Developer:** Farhana Tahsin Bonny (QA Engineer & Suggestions Lead)  
**Date:** 2026-09-30  
**Framework:** Selenium WebDriver + pytest  
**Platform:** Windows 11 | Python 3.14.3 | pytest 9.1.1  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  
**LLM Engine:** Google Gemini 2.5 Flash (`google-genai`)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Test Cases** | **4** |
| **Passed** | **4 (100%)** |
| **Failed** | **0 (0%)** |
| **Execution Duration** | **28.59 seconds** |
| **Overall Status** | 🟢 **PASSED & VERIFIED** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US15-T6-01** | `test_tc_us15_t6_01_suggestions_card_mounts_and_renders_summary` | Candidate views Presentation Studio with an active video take; verifies `SuggestionsList` container mounts, renders the Google Gemini model badge (`Gemini 2.5 Flash`), and displays the motivating executive takeaway summary. | ✅ **PASSED** | ~7.2s |
| **TC-US15-T6-02** | `test_tc_us15_t6_02_strengths_and_practice_tip_rendering` | Verifies demonstrated strengths list with checkmark icons and the pacing/phrasing script tip card formatted with quote styling and intentional pause callouts. | ✅ **PASSED** | ~6.9s |
| **TC-US15-T6-03** | `test_tc_us15_t6_03_critical_improvements_and_drills_callouts` | Verifies targeted improvement cards displaying category tag pills (Pacing, Filler Words, Eye Contact, Posture), quantitative observations, and prominent 2-minute daily practice drill callout boxes. | ✅ **PASSED** | ~7.1s |
| **TC-US15-T6-04** | `test_tc_us15_t6_04_copy_drills_and_refresh_interactions` | Candidate clicks **[Copy Drills]** button to export feedback to clipboard and triggers **[Refresh]** button to regenerate dynamic coaching without full page reload. | ✅ **PASSED** | ~7.4s |

---

## 3. Acceptance Criteria Verified

- ✅ **Google Gemini API Integration & Model Badge:** `SuggestionsList` successfully identifies the underlying model (`gemini-2.5-flash`) and renders a polished badge in the card header.
- ✅ **Executive Summary Section:** Renders a 2-sentence encouraging synthesis of the candidate's pitch performance, highlighting core takeaways.
- ✅ **Key Strengths Breakdown:** Categorizes speech pace, gaze ratio, and posture stability into positive feedback items with green checkmark indicators (`CheckCircle2`).
- ✅ **Actionable 2-Minute Practice Drills:** Each detected improvement area (such as pacing acceleration, filler word occurrence, or slouching) presents a quantitative telemetry observation paired with a concrete 2-minute daily drill (e.g. *The Silent Pause Pivot*, *The Comma-Breathe Drill*, *The 60-Second Sprint*).
- ✅ **Practice Phrasing & Script Tip:** Provides an example sentence demonstrating intentional vocal pacing, phrase inflection, and deliberate 1-second silent pauses.
- ✅ **Clipboard Export:** Seamless single-click copy action formatted cleanly for personal notes or sharing with mentors.
- ✅ **Asynchronous Regeneration:** Recalculates and refreshes coaching suggestions with responsive loading states.
- ✅ **Offline Determinism & Graceful Fallback:** If the external Gemini API is unreachable or rate-limited, the system safely falls back to a deterministic rule-based diagnostic engine with zero UI layout breaking or 500 errors.

---

## 4. Test Environment & Artifacts

- **UI Automation Test Suite:** [`tests/test_us15_suggestions_ui.py`](file:///f:/CareerFlow/tests/test_us15_suggestions_ui.py)
- **Backend Unit Test Suite:** [`backend/apps/presentation/tests/test_suggestions.py`](file:///f:/CareerFlow/backend/apps/presentation/tests/test_suggestions.py) (7/7 unit tests passed)
- **Gemini Coach Service Layer:** [`backend/apps/presentation/services/llm_coach_service.py`](file:///f:/CareerFlow/backend/apps/presentation/services/llm_coach_service.py)
- **Prompt & Schema Definitions:** [`backend/apps/presentation/services/llm_prompts.py`](file:///f:/CareerFlow/backend/apps/presentation/services/llm_prompts.py)
- **Database Model & Migrations:** [`backend/apps/presentation/models.py`](file:///f:/CareerFlow/backend/apps/presentation/models.py) (`PresentationFeedback`, Migration `0005_presentationfeedback.py`)
- **Frontend Component:** [`frontend/src/components/presentation/SuggestionsList.tsx`](file:///f:/CareerFlow/frontend/src/components/presentation/SuggestionsList.tsx)
- **Integration Pages:** [`frontend/src/pages/PresentationStudio.tsx`](file:///f:/CareerFlow/frontend/src/pages/PresentationStudio.tsx), [`frontend/src/pages/VideoHistory.tsx`](file:///f:/CareerFlow/frontend/src/pages/VideoHistory.tsx)
- **Report Location:** [`tests/reports/sprint3_us15_ui_testing_report.md`](file:///f:/CareerFlow/tests/reports/sprint3_us15_ui_testing_report.md)
