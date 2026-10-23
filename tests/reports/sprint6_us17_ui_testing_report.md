# Sprint 6 UI Testing Report — Task US-17-T6

**Sprint:** Sprint 6 (Epic 4: Video Presentation & AI)  
**User Story:** US-17: Score Trends Across Attempts (Chronological Performance Tracking, Trajectory Analytics & Comparative Curve Visualization)  
**Task:** US-17-T6 (Peer UI Testing, Tenant Isolation Verification & Automated Selenium Test Suite)  
**Author / Lead Developer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer)  
**Reviewer / UI Tester:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (from `feat/us-17-score-trends`)  
**Date of Testing:** 2026-10-23  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** macOS 26.6.2 (Darwin arm64) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us17_score_trends_ui.py`) in 93.54s | 🟢 **PASSED** |
| **Backend Unit & Security Tests** | **8 / 8 Passed (100%)** (`apps.presentation.tests.test_us17_score_trends`) in 3.33s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 1.61s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified & Enforced** | 🟢 **PASSED** |
| **Tenant Isolation & Security** | **100% Enforced** (Strict `request.user` partition on `/api/presentation/trends/`, zero score/transcript leakage) | 🛡️ **SECURE** |
| **UI Test Suite Duration** | **93.54 seconds** | ⏱️ **OPTIMAL** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us17_score_trends_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-17-01** | `test_tc17_01_tab_switching_and_navigation` | Student logs in and navigates to `/student/videos`; verifies tab button `[data-testid='tab-score-trends']` seamlessly activates the Score Trends analytics dashboard; verifies tab button `[data-testid='tab-takes-history']` returns to video takes; verifies direct URL access and deep-linking via `/presentation/trends` (AC 1 & AC 6). | ✅ **PASSED** | ~11.2s |
| **TC-17-02** | `test_tc17_02_zero_attempts_welcoming_state` | Student with 0 previous practice takes visits `/student/videos?tab=trends`; asserts welcoming zero-state card (`[data-testid='trends-zero-state']`), descriptive onboarding copy, and "Record Your First Practice Take" CTA button (`[data-testid='button-start-first-trend-take']`); clicks CTA and verifies immediate redirect to `/student/practice` (AC 4). | ✅ **PASSED** | ~11.5s |
| **TC-17-03** | `test_tc17_03_single_attempt_baseline_state` | Student with exactly 1 completed practice take (74/100) visits Score Trends; asserts `[data-testid='trends-single-baseline-state']` with "Baseline Take Registered" callout, overall baseline benchmark (74/100), speech dynamics, and visual presence baseline stats; verifies CTA `[data-testid='button-upload-second-take-cta']` navigates to `/student/practice` (AC 4). | ✅ **PASSED** | ~11.8s |
| **TC-17-04** | `test_tc17_04_multi_attempt_dashboard_and_summary` | Student with 3 chronological attempts (70 ➔ 78 ➔ 88) visits Score Trends; asserts `[data-testid='score-trends-dashboard']`, progress trajectory banner ("Across 3 Recorded Attempts"), total delta widget (+18%), 4 summary metric widgets (Latest: 88, Personal Best: 88, Average: 78.7, Baseline: 70), and contextual progress highlight badges (AC 1 & AC 3). | ✅ **PASSED** | ~12.4s |
| **TC-17-05** | `test_tc17_05_chart_series_toggle_interaction` | Asserts Recharts line graph container (`[data-testid='recharts-line-container']`); validates series toggle filter buttons: `[data-testid='toggle-chart-overall']`, `[data-testid='toggle-chart-categories']`, `[data-testid='toggle-chart-speech']`, `[data-testid='toggle-chart-behavioral']`, and `[data-testid='toggle-chart-all']`; verifies active toggle styling and chart curve responsiveness (AC 1 & AC 2). | ✅ **PASSED** | ~11.6s |
| **TC-17-06** | `test_tc17_06_milestone_cards_and_navigation` | In multi-attempt view, asserts Historical Take Milestones section: verifies Take #1 displays "Starting Baseline", Take #2 displays "+12% vs baseline"; clicks `[data-testid='milestone-take-card-1']` and verifies clean navigation / modal opening for the selected session report (AC 3 & AC 6). | ✅ **PASSED** | ~11.9s |
| **TC-17-07** | `test_tc17_07_tenant_isolation_trend_privacy` | Student Alice has 3 practice takes (94 peak score). Student Bob has 1 practice take (64 score). Bob logs into Score Trends: asserts Bob only sees his baseline take (64) and never sees Alice's trend curves, scores, or confidential filenames (AC 5). | ✅ **PASSED** | ~11.4s |
| **TC-17-08** | `test_tc17_08_dynamic_curve_update_after_attempt` | Student starts with 1 baseline take (displays baseline state); a second practice attempt is completed; user re-fetches trends: asserts UI dynamically transitions to full `[data-testid='score-trends-dashboard']` with multi-attempt curve and +12% delta (AC 6). | ✅ **PASSED** | ~11.7s |

---

### B. Backend Security & Unit Tests (`backend/apps/presentation/tests/test_us17_score_trends.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_tc17_01_no_attempts_returns_informative_empty_state_200_ok` | Verifies student with 0 completed attempts receives HTTP 200 OK with empty `trend_points: []` and guidance message. | ✅ **PASSED** |
| `test_tc17_02_single_attempt_returns_baseline_trend_data` | Verifies student with 1 completed attempt receives baseline metrics and prompt for second attempt (`progress_status: BASELINE`). | ✅ **PASSED** |
| `test_tc17_03_multiple_attempts_chronological_ordering_and_deltas` | Verifies multiple attempts are aggregated chronologically (Attempt 1 ➔ 2 ➔ 3) with exact delta calculations and summary statistics. | ✅ **PASSED** |
| `test_tc17_04_tenant_isolation_students_only_see_own_trends` | Verifies Student A only receives their own scores in the trends aggregation, never Student B's. | ✅ **PASSED** |
| `test_tc17_05_unauthenticated_access_rejected_401` | Verifies unauthenticated GET calls to `/api/presentation/trends/` return HTTP 401 Unauthorized. | ✅ **PASSED** |
| `test_tc17_06_in_progress_or_failed_videos_excluded_from_trends` | Verifies processing or failed videos without completed scores are excluded from score trends. | ✅ **PASSED** |
| `test_tc17_07_declining_score_trend_computes_negative_delta` | Verifies declining performance trajectory produces negative delta (`-10%`) and `progress_status: DECLINED`. | ✅ **PASSED** |
| `test_tc17_08_sub_metrics_included_for_each_trend_point` | Verifies each trend point includes pace, filler score, eye contact score, posture, engagement, and speech WPM. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verification

### ✅ AC 1: Dashboard displays the overall score trend across attempts
- **Verification:** When a student has 2 or more completed practice takes, `ScoreTrendsDashboard` displays the Recharts line graph (`[data-testid='recharts-line-container']`). The "Overall Score" series connects chronological attempts with color-coded points, accompanied by the Total Delta widget and summary stat cards.
- **Evidence:** Verified in automated UI tests `TC-17-04`, `TC-17-05` and backend unit test `test_tc17_03`.

### ✅ AC 2: Category scores (speech and behavioral) are shown as separate comparative trends
- **Verification:** The series filter pills allow students to toggle comparative category curves:
  1. **Speech vs. Behavioral (`[data-testid='toggle-chart-categories']`):** Renders Speech score line (blue `#3a6384`) and Behavioral score line (amber `#b89c3b`).
  2. **Vocal Dynamics (`[data-testid='toggle-chart-speech']`):** Renders Pacing Cadence score and Filler Word Control score.
  3. **Visual Presence (`[data-testid='toggle-chart-behavioral']`):** Renders Eye Contact score, Posture Stability, and Expressive Engagement.
  4. **All Curves (`[data-testid='toggle-chart-all']`):** Displays all metrics on a single comparative canvas.
- **Evidence:** Verified in automated UI test `TC-17-05` and backend unit test `test_tc17_08`.

### ✅ AC 3: Trends are built from stored previous analysis results chronologically
- **Verification:** The backend endpoint `PresentationScoreTrendsView` queries completed videos ordered by `uploaded_at ASC`. Each point is assigned a sequential `attempt: 1, 2, 3...` with full sub-model metrics (`presentation_score`, `speech_analysis`, `behavioral_analysis`). Historical milestone cards display chronologically from baseline.
- **Evidence:** Verified in automated UI tests `TC-17-04`, `TC-17-06` and backend unit test `test_tc17_03`.

### ✅ AC 4: Dashboard handles students with one attempt or no attempts with informative feedback
- **Verification:** 
  1. **Zero Attempts (`[data-testid='trends-zero-state']`):** Displays a welcoming card with a clear illustration, explanatory copy, and a primary CTA linking to `/student/practice`.
  2. **Single Attempt Baseline (`[data-testid='trends-single-baseline-state']`):** Renders a "Baseline Take Registered" card with the student's initial score (e.g. 74/100), speech metrics, visual presence breakdown, and a callout prompting a second take to unlock the improvement curve.
- **Evidence:** Verified in automated UI tests `TC-17-02`, `TC-17-03` and backend unit tests `test_tc17_01`, `test_tc17_02`.

### ✅ AC 5: Students only see their own trends (strict tenant isolation)
- **Verification:** `PresentationScoreTrendsView` filters exclusively by `request.user`: `PresentationVideo.objects.filter(user=request.user, status='COMPLETED')`. Foreign students cannot inspect or aggregate another student's practice scores. Tested with Alice and Bob: Bob only sees his baseline take (64), with zero leakage of Alice's data.
- **Evidence:** Verified in automated UI test `TC-17-07` and backend unit test `test_tc17_04`.

### ✅ AC 6: Dashboard updates dynamically after each new attempt completes
- **Verification:** Tested tab switching between Video Takes and Score Trends on `/student/videos`. Verified that when a new attempt is completed, the trends view immediately re-aggregates, transitioning from single baseline mode to multi-attempt curve mode with updated total deltas and personal best metrics.
- **Evidence:** Verified in automated UI tests `TC-17-01`, `TC-17-06`, `TC-17-08`.

---

## 4. UI Testing Evidence & Screenshots

All 8 screenshots were automatically captured during the live Selenium execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us17_01_tab_switching_and_navigation.png`](screenshots/us17_01_tab_switching_and_navigation.png) | Step 1: Tab Switching & Navigation | Demonstrates tab button switching between "Video Takes" and "Score Trends & Progress (Analytics)" on `/student/videos`. |
| [`us17_02_zero_attempts_welcoming_state.png`](screenshots/us17_02_zero_attempts_welcoming_state.png) | Step 2: Zero Attempts Empty State | Displays clean zero-state card (`trends-zero-state`), onboarding explanation, and "Record Your First Practice Take" CTA button. |
| [`us17_03_single_attempt_baseline_state.png`](screenshots/us17_03_single_attempt_baseline_state.png) | Step 3: Single Attempt Baseline State | Demonstrates baseline benchmark card (74/100), speech dynamics, visual presence, and "Record Second Attempt to Unlock Trends" CTA. |
| [`us17_04_multi_attempt_dashboard_and_summary.png`](screenshots/us17_04_multi_attempt_dashboard_and_summary.png) | Step 4: Multi-Attempt Score Trends Dashboard | Demonstrates progress trajectory banner, +18% total delta badge, 4 summary stat cards (Latest, Personal Best, Average, Baseline), and highlight chips. |
| [`us17_05_chart_series_toggle_interaction.png`](screenshots/us17_05_chart_series_toggle_interaction.png) | Step 5: Chart Series Toggles & Curve Switching | Shows interactive series toggle pills (Overall, Speech vs. Behavioral, Vocal Dynamics, Visual Presence, All Curves) on Recharts graph. |
| [`us17_06_milestone_cards_and_navigation.png`](screenshots/us17_06_milestone_cards_and_navigation.png) | Step 6: Historical Milestone Take Cards | Demonstrates chronological milestone cards (Take #1 Baseline, Take #2 +12% vs baseline) linking directly to session reports. |
| [`us17_07_tenant_isolation_trend_privacy.png`](screenshots/us17_07_tenant_isolation_trend_privacy.png) | Step 7: Strict Tenant Isolation on Trends | Demonstrates that Bob only sees his beginner baseline take (64/100) and Alice's confidential scores and takes are completely hidden. |
| [`us17_08_dynamic_curve_update_after_attempt.png`](screenshots/us17_08_dynamic_curve_update_after_attempt.png) | Step 8: Dynamic Curve Update After New Attempt | Demonstrates seamless transition from single baseline mode to multi-attempt curve (+12% delta) when a second take is recorded. |

---

## 5. Architecture & Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCORE TRENDS & PROGRESS ANALYTICS                        │
│                 Chronological Telemetry & Trajectory Engine                 │
└─────────────────────────────────────────────────────────────────────────────┘
                               Student Request
                                      │
                                      ▼
                        GET /api/presentation/trends/
                                      │
                        [Authentication & Tenant Guard]
                        └── Filter: user = request.user
                        └── Filter: status = 'COMPLETED'
                        └── Order: uploaded_at ASC
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
        Total Takes < 2                               Total Takes >= 2
  ┌─────────────────────────┐                   ┌─────────────────────────┐
  │ Case 1: 0 attempts      │                   │ Compute Trend Points:   │
  │ └── progress: 'NO_DATA' │                   │ └── attempt: 1, 2, ...N │
  │ └── Empty state CTA     │                   │ └── sub-scores (speech, │
  ├─────────────────────────┤                   │     behavioral, pace)   │
  │ Case 2: 1 attempt       │                   │ Compute Total Deltas:   │
  │ └── progress: 'BASELINE'│                   │ └── overall_delta (%)   │
  │ └── Baseline Benchmark  │                   │ └── pace_delta, etc.    │
  │ └── Prompt for 2nd take │                   │ Compute Summary Stats:  │
  └─────────────────────────┘                   │ └── Latest, Max, Mean   │
                                                └─────────────────────────┘
                                                             │
                                                             ▼
                                                Frontend Recharts Rendering:
                                                - Overall Curve (Emerald)
                                                - Speech vs Behavioral
                                                - Vocal Dynamics (Pace/Filler)
                                                - Visual Presence (Eye/Posture)
                                                - Milestone Take Cards
```

---

## 6. Testing Observations & Resolutions

### Observation: Tailwind CSS Text Transform in Headless DOM
- **Symptom:** During initial test execution of TC-17-03 and TC-17-04, text assertions for `"Baseline Take Registered"` and `"Latest Take"` evaluated against the rendered uppercase DOM text (`"BASELINE TAKE REGISTERED"`, `"LATEST TAKE"`).
- **Root Cause:** Tailwind CSS class `uppercase` on the label elements transforms the inner text in the browser's rendered accessibility tree.
- **Resolution:** Updated test assertions in `tests/test_us17_score_trends_ui.py` to compare against `.upper()` rendered strings.
- **Outcome:** Clean, resilient test execution with 100% determinism across headless Chrome runs.

---

## 7. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit & Security Tests:** 8/8 passed (`python backend/manage.py test apps.presentation.tests.test_us17_score_trends`) in 3.33s
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors in 1.61s (`npm run build`)
- [x] **Automated Selenium UI Tests:** 8/8 test cases passed in 93.54s (`pytest tests/test_us17_score_trends_ui.py`)
- [x] **Acceptance Criteria Verification:** AC 1 through AC 6 fully verified and documented
- [x] **Tenant Isolation Security:** Verified strict user partition with zero cross-student data leakage
- [x] **Edge Case Verification:** Verified both 0 attempts (welcoming empty state) and 1 attempt (baseline benchmark)
- [x] **Visual Evidence Captured:** 8 high-resolution screenshots archived in `tests/reports/screenshots/`
- [x] **Git Cleanliness:** No commits or pushes performed during testing, strictly maintaining review policy

---

## 8. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
> **Target Branch:** `develop`  
> **Summary Statement:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) has engineered a powerful, mathematically sound, and visually engaging trajectory tracking dashboard for US-17. The edge-case handling for 0 attempts and 1 baseline attempt provides clear guidance to new students, while the multi-attempt Recharts visualization and series toggles offer actionable insights into vocal dynamics and visual presence. All 8 backend unit tests and 8 automated Selenium UI tests execute cleanly with a 100% pass rate. The feature is approved and ready for merge into `develop`.
