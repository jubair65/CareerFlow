# Sprint 3 UI Testing Report — Task US-14-T5

**Sprint:** Sprint 3 (Presentation AI)  
**User Story:** US-14: Video Presentation Score  
**Task:** US-14-T5 (UI Testing for Score Display Screen)  
**Tester / Developer:** Jannatun Naeem Mona (System Analyst / BA)  
**Date:** 2026-09-30  
**Framework:** Selenium WebDriver + pytest  
**Platform:** Windows 11 | Python 3.14.4 | pytest 9.1.1  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Test Cases** | **4** |
| **Passed** | **4 (100%)** |
| **Failed** | **0 (0%)** |
| **Execution Duration** | **41.09 seconds** |
| **Overall Status** | 🟢 **PASSED & VERIFIED** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US14-T5-01** | `test_tc_us14_t5_01_scorecard_renders_with_overall_score` | Candidate navigates to Presentation Studio with an active video take; verifies PresentationScoreCard renders with circular SVG animated gauge, composite score value (0–100), and color-coded status badge (`Excellent` / `Competent` / `Needs Practice`). | ✅ **PASSED** | ~10.2s |
| **TC-US14-T5-02** | `test_tc_us14_t5_02_subcategory_diagnostics_breakdown` | Verifies dual pillar breakdown cards (Speech Delivery 50% & Behavioral Poise 50%) and detailed subcategory progress bars for Speaking Pace, Filler Words, Eye Contact, Posture Stability, and Facial Engagement. | ✅ **PASSED** | ~9.8s |
| **TC-US14-T5-03** | `test_tc_us14_t5_03_recalculate_score_interaction` | Candidate triggers real-time score recalculation via `[data-testid='button-recalculate-score']`; verifies asynchronous state transition, API call to `/api/presentation/<video_id>/score/`, and reactive card update without page reload. | ✅ **PASSED** | ~10.4s |
| **TC-US14-T5-04** | `test_tc_us14_t5_04_graceful_degradation_banner_rendering` | Evaluates system behavior when video frames lack computer vision landmarks; verifies graceful degradation banner (`[data-testid='degradation-warning-banner']`) is displayed and overall score defaults to 100% speech weighting (US-40 alignment). | ✅ **PASSED** | ~10.7s |

---

## 3. Acceptance Criteria Verified

- ✅ **Composite Score & Circular Gauge UI:** `PresentationScoreCard` successfully mounts in both `PresentationStudio` and the `VideoHistory` analysis modal. The circular animated SVG gauge accurately reflects the 0–100 integer score with smooth circumference stroke transitions.
- ✅ **Grade Badge Classification:** The evaluation tiers map accurately according to the specification:
  - 🟢 **Excellent (85–100):** `#277254` green badge with executive presence narrative.
  - 🟡 **Competent (70–84):** `#d97706` amber badge with polish guidance.
  - 🔴 **Needs Practice (< 70):** `#dc2626` coral badge with drill recommendations.
- ✅ **Dual-Pillar Matrix (50% / 50%):** 
  - **Speech Delivery (50%):** Pacing (optimal 130–160 WPM) and Filler Word Control (-5 pts per filler).
  - **Behavioral Poise (50%):** Eye contact camera gaze ratio (40%), Posture stability (30%), and Facial engagement (30%).
- ✅ **Subcategory Diagnostic Bars:** All 5 subcategory performance progress bars render with quantitative labels and benchmark guidance.
- ✅ **Recalculate Score Action:** The candidate can trigger on-demand score recalculation without UI jitter or layout shifts.
- ✅ **Graceful Degradation Resilience (US-40):** When behavioral metrics are missing due to corrupted frames or lighting issues, the UI displays an informative alert and recalculates overall score on 100% speech clarity rather than failing or showing zero.

---

## 4. Test Environment & Artifacts

- **UI Test Suite:** [`tests/test_us14_presentation_scoring_ui.py`](file:///e:/projectSWE/CareerFlow/tests/test_us14_presentation_scoring_ui.py)
- **Unit Test Suite:** [`backend/apps/presentation/tests/test_scoring.py`](file:///e:/projectSWE/CareerFlow/backend/apps/presentation/tests/test_scoring.py) (14/14 unit tests passed)
- **Scoring Engine Service:** [`backend/apps/presentation/services/scorer.py`](file:///e:/projectSWE/CareerFlow/backend/apps/presentation/services/scorer.py)
- **Frontend Component:** [`frontend/src/components/presentation/PresentationScoreCard.tsx`](file:///e:/projectSWE/CareerFlow/frontend/src/components/presentation/PresentationScoreCard.tsx)
- **Scoring Specification:** [`docs/sprint3_us14_scoring_specification.md`](file:///e:/projectSWE/CareerFlow/docs/sprint3_us14_scoring_specification.md)
- **Report Location:** [`tests/reports/sprint3_us14_ui_testing_report.md`](file:///e:/projectSWE/CareerFlow/tests/reports/sprint3_us14_ui_testing_report.md)
