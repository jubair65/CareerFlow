# Sprint 5 UI Testing Report — Task US-10-T6

**Sprint:** Sprint 5 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Human Review)  
**Epic:** Epic 2: CV Analysis & Job Matching  
**User Story:** US-10: View Applicant CV Match Scores  
**Task:** US-10-T6 (Peer UI Testing & Code Review for Applicant CV Scores Display Screens)  
**Author / Developer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Software Developer)  
**Reviewer / UI Tester:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (Squash and Merge upon approval)  
**Date of Testing:** 2026-10-16  
**Test Framework:** Selenium WebDriver + pytest & Django REST Framework APITestCase  
**Platform:** macOS 26.6.2 (Darwin arm64) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.40`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **6 / 6 Passed (100%)** (`tests/test_us10_applicant_cv_scores_ui.py`) | 🟢 **PASSED** |
| **Backend Unit Tests** | **10 / 10 Passed (100%)** (`backend/apps/recruitment/tests/test_us10_cv_scores.py`) | 🟢 **PASSED** |
| **Frontend TypeScript Build** | **Built in 1.27s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified** | 🟢 **PASSED** |
| **Defects Caught & Documented** | **1** (React controlled search input clearing in automated testing harness resolved) | 🛠️ **RESOLVED** |
| **UI Test Suite Duration** | **125.88 seconds (~2m 05s)** | ⏱️ **OPTIMAL** |
| **Backend Unit Test Duration** | **10.68 seconds** | ⏱️ **FAST** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us10_applicant_cv_scores_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US10-01** | `test_tc_us10_01_dashboard_dropdown_opens_modal` | HR logs into `/login`; navigates to HR Dashboard (`/hr/dashboard`); locates the quick room selector dropdown (`select-room-cv-scores-dashboard`); selects an active recruitment room; verifies modal mounts (`modal-room-cv-scores`); asserts room title and company header display accurately; cleanly dismisses via close button (X). | ✅ **PASSED** | ~13.7s |
| **TC-US10-02** | `test_tc_us10_02_room_card_action_button_opens_modal` | HR navigates to Recruitment Rooms list (`/hr/rooms`); locates room card; clicks the green "CV Scores" action button (`button-action-cv-scores-{room.id}`); verifies modal mount and asserts all 4 top metric cards: Total Applicants (4), Evaluated CVs (3), Average CV Score (~64%), and Top Match Score (88%). | ✅ **PASSED** | ~17.5s |
| **TC-US10-03** | `test_tc_us10_03_score_tier_badges_and_chips_rendering` | Inspects candidate table rows (`row-applicant-cv-{id}`); verifies color-coded score tags: Strong Match (88% green, Alice), Moderate Match (62% amber, Bob), Low Match (42% red, Charlie), and No CV Uploaded ("No CV" neutral gray, David); validates keyword coverage percentages and matched/missing skill chips without layout overflow. | ✅ **PASSED** | ~17.2s |
| **TC-US10-04** | `test_tc_us10_04_instant_search_and_tier_filtering` | Tests search filter input (`input-search-cv-scores`): verifies search by candidate name ("Alice"), candidate email, and unique matched skill ("Redux"); verifies tier filter tabs (`≥75%`, `50-74%`, `<50%`, `No CV`) filter candidate rows accurately; verifies filter reset to `All` restores complete roster. | ✅ **PASSED** | ~24.1s |
| **TC-US10-05** | `test_tc_us10_05_skill_breakdown_inspection_modal` | Clicks "Inspect" action button on candidate row; verifies CV Match Breakdown modal mounts (`modal-cv-skill-breakdown`); asserts candidate name header, overall match score gauge (88%), match tier badge ("Strong Match"); verifies 4 competency sub-signals with progress bars; verifies matched skills (green pills) and missing skills (red outline pills); verifies AI insights (strengths/gaps) and CV download link. | ✅ **PASSED** | ~18.8s |
| **TC-US10-06** | `test_tc_us10_06_empty_state_and_edge_cases` | Verifies empty state handling: opens CV scores for an active recruitment room with 0 applicants; verifies empty state card (`card-empty-cv-scores`) renders with clear explanatory message; verifies metrics show 0 Total and 0 Evaluated applicants; verifies RBAC isolation preventing access to unowned rooms. | ✅ **PASSED** | ~16.4s |

---

### B. Backend Unit Tests (`backend/apps/recruitment/tests/test_us10_cv_scores.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_get_cv_scores_as_room_owner_success` | Verifies room owner HR can retrieve room applicant CV scores, aggregates (average, top, lowest), and candidates list. | ✅ **PASSED** |
| `test_alias_endpoint_applicant_cv_scores` | Verifies backward-compatible alias endpoint `GET /api/recruitment/rooms/{id}/applicant-cv-scores/` returns identical payload. | ✅ **PASSED** |
| `test_applicant_without_cv_handled_gracefully` | Verifies applicants who submitted without a CV document return `has_cv=False`, `match_score=None`, and explanatory gap notes. | ✅ **PASSED** |
| `test_single_applicant_cv_score_detail` | Verifies single-applicant detail endpoint `GET /api/recruitment/rooms/{id}/cv-scores/{app_id}/` returns deep skill breakdown. | ✅ **PASSED** |
| `test_single_applicant_cv_score_not_found` | Verifies non-existent application in room returns HTTP 404 Not Found. | ✅ **PASSED** |
| `test_unauthenticated_user_cannot_view_scores` | Verifies unauthenticated requests are rejected with HTTP 401 Unauthorized. | ✅ **PASSED** |
| `test_student_user_cannot_view_scores` | Verifies student candidates cannot access room CV scores, returning HTTP 403 Forbidden. | ✅ **PASSED** |
| `test_other_hr_cannot_view_scores_of_another_room` | Verifies strict room ownership RBAC: HR user cannot access applicant scores for another HR's room (HTTP 404). | ✅ **PASSED** |
| `test_search_filter_by_candidate_name_or_skill` | Verifies query parameters `?search=alice` and `?search=redux` filter backend results correctly. | ✅ **PASSED** |
| `test_min_score_filter` | Verifies query parameter `?min_score=80` filters applicants to only those with scores >= 80. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verification

### ✅ AC-1: HR can view the CV Match Score of each applicant in their Room
- **Verification:** Navigating to `/hr/rooms` and clicking "CV Scores" displays all applicant submissions for that room in a clean table. Each applicant displays their calculated semantic match score percentage (e.g. `88%`, `62%`, `42%`).
- **Evidence:** Verified in automated test `TC-US10-02` and `TC-US10-03`.

### ✅ AC-2: Detailed CV score breakdown is available in an interactive modal
- **Verification:** Clicking the "Inspect" button (`button-view-breakdown-{id}`) on any candidate opens `CvSkillBreakdownModal`. The modal provides:
  1. Score gauge circle with percentage and match tier badge ("Strong Match", "Moderate Match", "Low Match").
  2. 4 competency sub-signals: **Domain & Craft**, **Collaboration**, **Ownership & Scope**, and **Standards & Quality** with animated progress bars.
  3. Matched skills rendered in solid green pills (`card-matched-skills`).
  4. Missing skills rendered in red-bordered outline pills (`card-missing-skills`).
  5. AI evaluation insights (bulleted strengths and actionable gap recommendations).
  6. Direct candidate CV download link.
- **Evidence:** Verified in automated test `TC-US10-05`.

### ✅ AC-3: Strict room ownership RBAC enforced (`IsRoomOwnerOrAdmin`)
- **Verification:** Only the HR Manager who created the recruitment room or an Agency Admin can view applicant scores. Unauthenticated users receive `401 Unauthorized`, Student accounts receive `403 Forbidden`, and other HR users cannot access rooms they do not own (returns `404 Not Found`).
- **Evidence:** Verified in unit tests `test_unauthenticated_user_cannot_view_scores`, `test_student_user_cannot_view_scores`, and `test_other_hr_cannot_view_scores_of_another_room`.

### ✅ AC-4: Scores and room selection accessible directly on HR Dashboard and Room Cards
- **Verification:** 
  1. **HR Dashboard (`/hr/dashboard`):** Features a dedicated "Inspect Room CV Scores..." dropdown (`select-room-cv-scores-dashboard`) with a prominent "US-10 Active" badge. Selecting any room immediately opens the CV scores modal.
  2. **Room Cards (`/hr/rooms`):** Active room cards display a green "CV Scores" action button (`button-action-cv-scores-{room.id}`) alongside "Copy Link".
- **Evidence:** Verified in automated tests `TC-US10-01` and `TC-US10-02`.

### ✅ AC-5: Applicants without uploaded CV or pending evaluation handled gracefully
- **Verification:** Candidates who applied without a CV document (e.g., pending submission) are displayed with a neutral gray "No CV" badge and `—` keyword coverage. The breakdown modal displays an informative warning banner: *"Evaluation Pending or Incomplete: This applicant does not yet have a computed CV match score."* No system errors or null reference crashes occur.
- **Evidence:** Verified in automated test `TC-US10-03` and backend test `test_applicant_without_cv_handled_gracefully`.

### ✅ AC-6: Responsive design, keyword coverage bars, tier filter tags, and instant search
- **Verification:** 
  - Instant search filters candidates by name, email, or matched skill tags without page reload.
  - Tier filter tags (`All`, `≥75%`, `50-74%`, `<50%`, `No CV`) dynamically filter the visible candidate table.
  - Sorting dropdown supports sorting by Score (High to Low, Low to High), Date Applied, and Name (A-Z).
  - Clean responsive grid layout for metric cards and modal tables with no horizontal overflow.
- **Evidence:** Verified in automated test `TC-US10-04`.

---

## 4. UI Testing Evidence & Screenshots

All screenshots were automatically captured during the live test execution and are archived in `tests/reports/screenshots/`:

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us10_01_dashboard_cv_scores_dropdown_modal.png`](screenshots/us10_01_dashboard_cv_scores_dropdown_modal.png) | HR Dashboard Dropdown Trigger | Shows the quick room selector dropdown on `/hr/dashboard` and the resulting modal mount with full room context. |
| [`us10_02_room_card_cv_scores_modal_mount.png`](screenshots/us10_02_room_card_cv_scores_modal_mount.png) | Room Card Action Button & Metrics | Demonstrates the 4 top summary metric cards: Total Applicants (4), Evaluated CVs (3), Average CV Score (~64%), Top Score (88%). |
| [`us10_03_score_tier_badges_and_candidate_table.png`](screenshots/us10_03_score_tier_badges_and_candidate_table.png) | Tier Badges & Skill Pills Table | Demonstrates color-coded score tags (Strong in green, Moderate in yellow, Low in red, No CV in gray) and keyword coverage bars. |
| [`us10_04_instant_search_and_tier_filters.png`](screenshots/us10_04_instant_search_and_tier_filters.png) | Search & Tier Filter Controls | Demonstrates instant client-side filtering by name, email, and skill, with active tier pill highlighting. |
| [`us10_05_skill_breakdown_inspection_modal.png`](screenshots/us10_05_skill_breakdown_inspection_modal.png) | CV Match Breakdown Drawer | Shows overall match gauge (88%), 4 competency signal bars, green matched skill pills, red missing skill pills, and AI insights. |
| [`us10_06_empty_state_and_edge_cases.png`](screenshots/us10_06_empty_state_and_edge_cases.png) | Empty Applicant State | Shows friendly zero-state illustration and guidance when a room has 0 applicants. |

---

## 5. Defects Identified & Resolved

### Defect 1: React Controlled Input State Clearing in Cross-Platform Selenium
- **Symptom:** During automated UI testing of search filter clearing in TC-US10-04, standard `input.clear()` did not dispatch React's synthetic `change` event on macOS Chrome, causing subsequent tier filters to retain stale query text.
- **Root Cause:** React controlled inputs track internal `_valueTracker` state. When Selenium sends `.clear()` without keyboard events, React does not detect an input change event.
- **Resolution:** Implemented a robust helper function `clear_react_input(driver, element)` dispatching native `input` and `change` DOM events alongside keyboard select-all backspace (`COMMAND/CONTROL + A, BACKSPACE`).
- **Outcome:** TC-US10-04 passed with 100% determinism.

---

## 6. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit Tests:** 10/10 passed (`python manage.py test apps.recruitment.tests.test_us10_cv_scores`)
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors (`npm run build`)
- [x] **Automated Selenium UI Tests:** 6/6 test cases passed (`pytest tests/test_us10_applicant_cv_scores_ui.py`)
- [x] **Acceptance Criteria Verification:** AC-1 through AC-6 fully verified on the UI
- [x] **RBAC Security Compliance:** Strict room ownership and unauthenticated barriers enforced
- [x] **Code Quality & Aesthetics:** Matches CareerFlow design system (clean typography, color-coded tiers, responsive cards)
- [x] **Cross-Testing Approval:** Signed off by Nafisa Tabassum Maria (@Maria-07-222)

---

## 7. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222))  
> **Target Branch:** `develop`  
> **Notes:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) delivered an exceptionally well-engineered implementation for US-10. The bridge service aggregates scores dynamically with robust fallback handling, the modal interfaces are intuitive and responsive, and all unit and UI test suites execute cleanly.
