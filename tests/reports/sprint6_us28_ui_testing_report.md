# Sprint 6 UI Testing Report — Task US-28-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Human Review)  
**Epic:** Epic 6: Scoring, Ranking & Shortlisting  
**User Story:** US-28: Side-by-Side Applicant Comparison (Multi-Candidate Evaluation Matrix & Differential Analysis)  
**Task:** US-28-T6 (Dedicated Peer UI Testing, Multi-Tenant Access Verification & Automated Selenium Test Suite)  
**Author / Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect)  
**Reviewer / Peer UI Tester:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer & Dedicated Peer Tester)  
**Source Branch:** `feat/us-28-applicant-comparison`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-24  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.12 (venv) | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`136.0.7103.114`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us28_applicant_comparison_ui.py`) in 130.91s | 🟢 **PASSED** |
| **Backend Unit & Security Tests** | **11 / 11 Passed (100%)** (`backend/apps/recruitment/tests/test_us28_applicant_comparison.py`) in 40.44s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 36.24s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified & Enforced** | 🟢 **PASSED** |
| **Multi-Tenant Isolation & Security** | **100% Enforced** (Strict `created_by` room owner guard; foreign HR 404/403, Student 403, Unauth 401) | 🛡️ **SECURE** |
| **Design System Harmonization** | **100% Light Mode Compliant** (`#f4f6ef` canvas, `#ffffff` cards, `#277254` emerald, `#253142` text) | 🎨 **POLISHED** |
| **UI Test Suite Duration** | **130.91 seconds (~2m 10s)** | ⏱️ **OPTIMAL** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us28_applicant_comparison_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-28-01** | `test_tc28_01_candidate_selection_checkboxes_and_bar` | HR Manager logs in, opens Ranked Applicants Leaderboard modal; verifies comparison checkboxes (`[data-testid='checkbox-compare-{id}']`); selects 1 candidate and verifies sticky comparison action bar mounts (`[data-testid='bar-candidate-comparison-selection']`) with "1 of 4 candidates selected" and disabled "Compare Now" button; selects 2nd candidate and asserts counter updates to "2 of 4 candidates selected" and "Compare Now" button becomes active and clickable (AC#1, AC#5). | ✅ **PASSED** | ~15.2s |
| **TC-28-02** | `test_tc28_02_max_selection_limit_enforcement` | Verifies selection bounds: HR selects 4 candidates; asserts counter displays "4 of 4 candidates selected"; verifies unselected 5th candidate checkbox is disabled with explanatory tooltip preventing over-selection; clicks "Clear" button (`[data-testid='btn-clear-comparison-selection']`) and asserts all checkboxes uncheck and floating selection bar dismisses cleanly (AC#1, AC#5). | ✅ **PASSED** | ~14.8s |
| **TC-28-03** | `test_tc28_03_launch_side_by_side_comparison_modal` | HR selects 2 top candidates and clicks "Compare Now"; asserts Applicant Comparison Modal mounts (`[data-testid='modal-applicant-comparison']`); verifies room title header, candidate counter chip, summary metrics banner ("Comparing 2 Candidates", Highest: 88.0, Avg: 87.0), and individual candidate column cards (`[data-testid='card-comparison-candidate-{id}']`) (AC#1, AC#2). | ✅ **PASSED** | ~16.5s |
| **TC-28-04** | `test_tc28_04_score_breakdown_and_group_differentials` | Inspects multi-modal score section across candidate cards: verifies Final Composite Score, CV Match Score, and Video Presentation Score meters; asserts "Best In" trophy badges (`[data-testid='badge-best-in-final_score']`, `[data-testid='badge-best-in-cv_score']`, `[data-testid='badge-best-in-video_score']`) visually highlighting category leaders with emerald border highlights (AC#2, AC#4). | ✅ **PASSED** | ~15.9s |
| **TC-28-05** | `test_tc28_05_cv_semantic_skills_match_matrix` | Inspects semantic skills comparison breakdown (`[data-testid='matrix-skills-breakdown']`): verifies matched skills pills with green checkmarks (`✓ Python`, `✓ Django`, `✓ AWS`) and missing required skills warning chips; asserts keyword coverage percentage meters across compared applicants (AC#3). | ✅ **PASSED** | ~15.6s |
| **TC-28-06** | `test_tc28_06_video_presentation_and_behavioral_signals` | Inspects video presentation metrics section: validates Speaking Pace WPM (`[data-testid='metric-wpm-{id}']`), Eye Contact % (`[data-testid='metric-eye-contact-{id}']`), Posture Stability %, and Filler Word Count; asserts eye contact leader trophy badge (`[data-testid='badge-best-in-eye_contact']`) and optimal pace tags (AC#3, AC#4). | ✅ **PASSED** | ~16.1s |
| **TC-28-07** | `test_tc28_07_graceful_missing_scores_handling` | Tests comparison including Candidate 5 with pending video evaluation: asserts modal mounts without errors; verifies pending metrics render as `"N/A - Pending"` with neutral badges; ensures visual layout and differential flags gracefully degrade without crashing or breaking adjacent candidate cards (AC#5). | ✅ **PASSED** | ~16.8s |
| **TC-28-08** | `test_tc28_08_tenant_isolation_unauthorized_room_owner_blocked` | Tests multi-tenant isolation: HR Bob attempts to compare applicants from HR Maria's private room; verifies backend API strictly rejects request with HTTP 404/403; verifies `comparison_service.compare_room_applicants` enforces `PermissionDenied`; ensures zero cross-tenant leakage of candidate scores, transcripts, or video signals (AC#6). | ✅ **PASSED** | ~17.1s |

---

### B. Backend Unit & Security Tests (`backend/apps/recruitment/tests/test_us28_applicant_comparison.py`)

| Test Method Name | Description | Status | Duration |
| :--- | :--- | :---: | :---: |
| `test_compare_applicants_valid_two_candidates` | Verifies comparing 2 valid candidates returns HTTP 200 OK with unified side-by-side comparison matrix, sub-scores, and differential flags. | ✅ **PASSED** | ~3.8s |
| `test_compare_applicants_valid_four_candidates_boundary` | Verifies upper boundary (4 candidates) returns complete metrics, highest score (88.0), and average score (82.2). | ✅ **PASSED** | ~3.9s |
| `test_compare_applicants_too_few_boundary` | Verifies lower boundary enforcement (<2 candidates) returns HTTP 400 Bad Request. | ✅ **PASSED** | ~3.5s |
| `test_compare_applicants_too_many_boundary` | Verifies upper boundary enforcement (>4 candidates) returns HTTP 400 Bad Request. | ✅ **PASSED** | ~3.7s |
| `test_compare_applicants_empty_ids_rejected` | Verifies empty candidate ID list returns HTTP 400 Bad Request. | ✅ **PASSED** | ~3.4s |
| `test_compare_applicants_duplicates_collapsing_below_minimum` | Verifies duplicate IDs (`[101, 101]`) collapse to 1 unique ID and are rejected with HTTP 400. | ✅ **PASSED** | ~3.5s |
| `test_compare_applicants_foreign_room_application_rejected` | Verifies candidates belonging to another recruitment room cannot be compared; returns HTTP 400. | ✅ **PASSED** | ~3.6s |
| `test_compare_applicants_unauthorized_hr_forbidden` | Verifies foreign HR Manager cannot access or compare applications in this room (HTTP 404 Not Found). | ✅ **PASSED** | ~3.7s |
| `test_compare_applicants_student_forbidden` | Verifies student/candidate users receive HTTP 403 Forbidden. | ✅ **PASSED** | ~3.6s |
| `test_compare_applicants_unauthenticated_forbidden` | Verifies unauthenticated requests receive HTTP 401 Unauthorized. | ✅ **PASSED** | ~3.5s |
| `test_compare_applicants_missing_scores_handled_gracefully` | Verifies candidates with missing/pending evaluations return `None` values and `TIER_PENDING` without null pointer exceptions. | ✅ **PASSED** | ~3.8s |

---

## 3. Acceptance Criteria Verification

### ✅ AC#1: Side-by-Side Comparison Modal Launch & Candidate Selection
- **Verification:** On `RankedApplicantsModal`, each candidate card features a dedicated comparison checkbox (`[data-testid='checkbox-compare-{id}']`). When at least 1 candidate is checked, the floating bottom action bar (`[data-testid='bar-candidate-comparison-selection']`) mounts smoothly showing the candidate counter ("X of 4 candidates selected"). The primary "Compare Now" action button is enabled only when between 2 and 4 candidates are checked. Clicking "Compare Now" immediately opens `ApplicantComparisonModal` (`[data-testid='modal-applicant-comparison']`) showing side-by-side comparative candidate cards.
- **Evidence:** Verified in automated UI tests `TC-28-01`, `TC-28-02`, `TC-28-03` and backend unit test `test_compare_applicants_valid_two_candidates`.

### ✅ AC#2: Multi-Modal Score Comparison
- **Verification:** The comparison modal aggregates and juxtaposes composite final scores, weighted CV match scores, and AI video presentation scores across all selected candidates. Visual score meters and progress bars render side-by-side with identical scales, enabling instant visual calibration between candidates.
- **Evidence:** Verified in automated UI test `TC-28-04` and backend unit tests `test_compare_applicants_valid_two_candidates`, `test_compare_applicants_valid_four_candidates_boundary`.

### ✅ AC#3: Granular Sub-Metric & Signal Comparison
- **Verification:**
  1. **CV Semantic Skills:** Displays required vs. matched skills pills (`✓ Python`, `✓ Django`, `✓ AWS`) and missing skills warning tags alongside keyword match percentage meters.
  2. **Video Dynamics:** Renders speaking pace (WPM with optimal pacing indicators), eye contact percentage meters, posture stability percentages, and filler word frequency counts.
- **Evidence:** Verified in automated UI tests `TC-28-05`, `TC-28-06` and backend unit test `test_compare_applicants_valid_two_candidates`.

### ✅ AC#4: Differential Analysis & Best-in-Category Visual Highlighting
- **Verification:** The comparison engine dynamically calculates leaders across all evaluation dimensions (`final_score`, `cv_score`, `video_score`, `eye_contact`, `skills_match`). Leading candidates receive gold trophy badges (`[data-testid='badge-best-in-{metric}']`), emerald accent borders, and differential callouts highlighting performance advantages over the cohort.
- **Evidence:** Verified in automated UI tests `TC-28-04`, `TC-28-06` and backend unit test `test_compare_applicants_valid_two_candidates`.

### ✅ AC#5: Graceful Handling of Missing Evaluations & Selection Boundaries
- **Verification:**
  1. **Missing Scores:** When a candidate has incomplete or pending evaluation results (e.g. video pending), scores render as `"N/A - Pending"` with neutral badges. No null pointer exceptions occur, and differential calculations omit null values safely.
  2. **Boundary Enforcement:** Strict 2 to 4 candidates limit enforced on both frontend (5th checkbox disabled, counter capped at 4) and backend (HTTP 400 if `< 2` or `> 4`).
- **Evidence:** Verified in automated UI tests `TC-28-02`, `TC-28-07` and backend unit tests `test_compare_applicants_too_few_boundary`, `test_compare_applicants_too_many_boundary`, `test_compare_applicants_missing_scores_handled_gracefully`.

### ✅ AC#6: Multi-Tenant Room Ownership & Access Security
- **Verification:** `compare_room_applicants` in `comparison_service.py` and `RecruitmentRoomViewSet.compare_applicants` enforce strict multi-tenant authorization:
  - Unauthenticated requests return `HTTP 401 Unauthorized`.
  - Non-HR users (students/candidates) receive `HTTP 403 Forbidden`.
  - Unauthorized HR Managers attempting to compare applicants in rooms they do not own receive `HTTP 404 Not Found` (or `PermissionDenied` at service level).
  - Attempting to pass applicant IDs belonging to a foreign room returns `HTTP 400 Bad Request`.
- **Evidence:** Verified in automated UI test `TC-28-08` and backend unit tests `test_compare_applicants_unauthorized_hr_forbidden`, `test_compare_applicants_student_forbidden`, `test_compare_applicants_foreign_room_application_rejected`.

---

## 4. UI Testing Evidence & Screenshots

All 8 high-resolution screenshots were captured during headless Chrome test execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us28_01_candidate_selection_checkboxes_and_bar.png`](screenshots/us28_01_candidate_selection_checkboxes_and_bar.png) | Step 1: Candidate Selection Checkboxes & Action Bar | Shows candidate checkboxes in `RankedApplicantsModal` with floating bottom bar showing "2 of 4 candidates selected" and enabled "Compare Now" action button. |
| [`us28_02_max_selection_limit_enforcement.png`](screenshots/us28_02_max_selection_limit_enforcement.png) | Step 2: Selection Limit Boundary (Max 4) & Clear Action | Demonstrates 4 candidates selected, 5th unselected checkbox disabled with tooltip, and "Clear" button ready to reset selection. |
| [`us28_03_launch_side_by_side_comparison_modal.png`](screenshots/us28_03_launch_side_by_side_comparison_modal.png) | Step 3: Side-by-Side Comparison Modal Mount | Displays full `ApplicantComparisonModal` in CareerFlow light mode with summary banner (Highest: 88.0, Avg: 87.0) and candidate profile cards. |
| [`us28_04_score_breakdown_and_group_differentials.png`](screenshots/us28_04_score_breakdown_and_group_differentials.png) | Step 4: Multi-Modal Score Comparison & Differentials | Highlights side-by-side Final, CV, and Video score meters with gold "Best In" trophy badges for Rahim Ahmed (Final, CV) and Fatima Noor (Video). |
| [`us28_05_cv_semantic_skills_match_matrix.png`](screenshots/us28_05_cv_semantic_skills_match_matrix.png) | Step 5: Semantic Skills Match & Keyword Matrix | Displays matched skills pills with green checkmarks (`✓ Python`, `✓ Django`, `✓ AWS`) alongside missing required skills badges. |
| [`us28_06_video_presentation_and_behavioral_signals.png`](screenshots/us28_06_video_presentation_and_behavioral_signals.png) | Step 6: Video Presentation & Behavioral Telemetry | Shows Speaking Pace (WPM), Eye Contact %, Posture Stability %, Filler Words, and Eye Contact Leader badge (`92% Eye Contact`). |
| [`us28_07_graceful_missing_scores_handling.png`](screenshots/us28_07_graceful_missing_scores_handling.png) | Step 7: Graceful Degradation for Pending Evaluations | Demonstrates Candidate 5 with incomplete video evaluation displaying `"N/A - Pending"` neutral badges without layout breakage or console errors. |
| [`us28_08_tenant_isolation_unauthorized_room_owner_blocked.png`](screenshots/us28_08_tenant_isolation_unauthorized_room_owner_blocked.png) | Step 8: Multi-Tenant Room Isolation & Access Guard | Verifies that foreign HR Managers are strictly blocked from comparing applicants in rooms they do not own (HTTP 404/403 enforced). |

---

## 5. Design Polish & CareerFlow Light Mode Harmonization

During dedicated peer review (`US-28-T6`), the applicant comparison interface was reviewed and aligned with CareerFlow's cohesive light-mode design system:

1. **Light Mode Background & Card Architecture:**
   - Replaced dark backgrounds (`bg-slate-900`, `bg-zinc-800`, dark gray panels) with clean white (`#ffffff`) candidate cards and light neutral surface canvas (`#f4f6ef`, `#fbfaf5`).
   - Replaced heavy borders with CareerFlow standard neutral dividers (`#d9dbd1` and `#ecefe7`).

2. **Typography & Readability:**
   - Updated headings and labels to CareerFlow deep slate navy (`#253142`), providing sharp contrast and WCAG 2.2 AA readability.
   - Secondary text styled in muted slate (`#4b5563` and `#6b7280`).

3. **Curated Color Tokens:**
   - **Primary Action & Counter:** Emerald green (`#277254`) for selection counter chips, active checkboxes, and progress meters.
   - **Leader Highlights:** Warm amber gold (`#b89c3b` and `bg-amber-50 text-amber-800 border-amber-200`) for "Best In" trophy badges and candidate differentiator highlights.
   - **Technical Signals:** Steel blue (`#3a6384`) for speech analysis and semantic keyword coverage meters.

4. **Selection Action Bar:**
   - Redesigned the sticky bottom floating comparison bar in `RankedApplicantsModal.tsx` with translucent backdrop blur (`bg-white/95 backdrop-blur-md`), `#d9dbd1` top border, and dark slate primary action button (`#253142` hover `#1b2432`).

---

## 6. Architecture & Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APPLICANT COMPARISON & DIFFERENTIALS                     │
│                  Multi-Candidate Cross-Evaluation Engine                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                HR Manager Request
                                       │
                                       ▼
                   POST /api/recruitment/rooms/{id}/compare-applicants/
                                       │
                      [Authorization & Multi-Tenant Guard]
                      ├── IsAuthenticated & IsHRManager
                      └── Filter: room.created_by == request.user (404/403)
                                       │
                                       ▼
                      [Candidate Selection Boundary Guard]
                      ├── 2 <= len(application_ids) <= 4 (400 if out of bounds)
                      └── All application_ids belong to room.id (400 if foreign)
                                       │
                                       ▼
                         comparison_service.py
                      ┌─────────────────────────────────┐
                      │ 1. Fetch Candidate Applications │
                      │ 2. Fetch CV Matches & Scores    │
                      │ 3. Fetch Presentation Scores    │
                      │ 4. Fetch Speech & Behavioral    │
                      └────────────────┬────────────────┘
                                       │
                                       ▼
                      [Compute Differentials & Best In]
                      ├── final_score max -> best_in["final_score"]
                      ├── cv_score max    -> best_in["cv_score"]
                      ├── video_score max -> best_in["video_score"]
                      ├── eye_contact max -> best_in["eye_contact"]
                      └── Missing scores  -> None, TIER_PENDING
                                       │
                                       ▼
                        HTTP 200 OK Comparison Matrix
                                       │
                                       ▼
                    ApplicantComparisonModal.tsx (Frontend)
                    ├── Header Summary (Highest, Average, Count)
                    ├── Side-by-Side Candidate Cards (Grid 2-4 cols)
                    ├── Multi-Modal Score Meters (Final, CV, Video)
                    ├── "Best In" Trophy Badges (Gold/Amber)
                    ├── Semantic Skills Match & Keyword Coverage
                    ├── Video Behavioral Telemetry (WPM, Eye Contact)
                    └── Graceful "N/A - Pending" State for missing data
```

---

## 7. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit & Security Tests:** 11/11 passed (`python manage.py test apps.recruitment.tests.test_us28_applicant_comparison`) in 40.44s
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors in 36.24s (`npm run build`, Vite v6.4.3)
- [x] **Automated Selenium UI Tests:** 8/8 test cases passed in 130.91s (`pytest tests/test_us28_applicant_comparison_ui.py`)
- [x] **Acceptance Criteria Verification:** AC#1 through AC#6 fully verified and documented
- [x] **Multi-Tenant Room Isolation:** Verified strict room owner authorization; foreign HR, student, unauthenticated blocked
- [x] **Boundary Enforcement:** Verified min 2, max 4 candidates limit on frontend and backend
- [x] **Graceful Degradation:** Verified missing/pending evaluations display `"N/A - Pending"` without errors
- [x] **Design Polish:** 100% compliant with CareerFlow light mode palette
- [x] **Visual Evidence Captured:** 8 high-resolution screenshots archived in `tests/reports/screenshots/`

---

## 8. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer & Dedicated Peer Tester)  
> **Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect)  
> **Target Branch:** `develop`  
> **Summary Statement:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) has implemented a comprehensive, highly robust applicant comparison feature for US-28. The multi-candidate matrix, boundary enforcement (2-4 candidates), semantic skills breakdown, video dynamics telemetry, and automated differential calculations provide exceptional decision support for hiring managers. All 11 backend unit tests and 8 automated Selenium UI tests execute with a 100% pass rate. The light-mode redesign seamlessly harmonizes with the CareerFlow visual design system. The feature is verified, signed off, and recommended for immediate merge into `develop`.
