# Sprint 5 UI Testing Report — Task US-25-T6

**Sprint:** Sprint 5 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Human Review)  
**Epic:** Epic 6: Applicant Scoring, Ranking & Shortlisting  
**User Story:** US-25: Automatic Candidate Shortlisting (Configurable Criteria & Automated Screening)  
**Task:** US-25-T6 (Peer UI Testing & Code Review for Automatic Shortlisting Flow)  
**Author / Developer:** Jannatun Naeem Mona ([@jn-mona04](https://github.com/jn-mona04)) (Systems Analyst / BA)  
**Reviewer / UI Tester:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) (Project Manager & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (PR #15, Commit `65f2051` merged via `0224ff3`)  
**Date of Testing:** 2026-10-21  
**Test Framework:** Selenium WebDriver + pytest & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.2 | pytest 9.1.1 | selenium 4.49.0  
**Environment:** Localhost (Frontend: `http://127.0.0.1:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us25_automatic_shortlisting_ui.py`) | 🟢 **PASSED** |
| **Backend Unit Tests** | **15 / 15 Passed (100%)** (`backend/apps/recruitment/tests/test_us25_shortlisting.py`) | 🟢 **PASSED** |
| **Frontend TypeScript Build** | **Built in 12.71s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified** | 🟢 **PASSED** |
| **Code Review Findings & Observations** | **4** (Documented below for developer review) | ℹ️ **NOTED** |
| **UI Test Suite Duration** | **143.24 seconds (~2m 23s)** | ⏱️ **OPTIMAL** |
| **Backend Unit Test Duration** | **66.77 seconds** | ⏱️ **FAST** |
| **Overall Recommendation** | **VERIFIED AND SIGNED OFF** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us25_automatic_shortlisting_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US25-01** | `test_tc_us25_01_dashboard_shortlist_dropdown_and_header_button` | HR logs into `/login`; navigates to HR Dashboard (`/hr/dashboard`); tests quick room selector dropdown (`select-room-shortlist-dashboard`) to select room; verifies modal mounts (`modal-shortlist-config`); asserts room title, company name, and US-25 badge; cleanly dismisses via close button (X); verifies quick action hero button (`button-view-shortlisted-dashboard`) also opens modal for active room. | ✅ **PASSED** | ~14.1s |
| **TC-US25-02** | `test_tc_us25_02_room_card_action_button_and_summary_statistics` | HR navigates to Recruitment Rooms list (`/hr/rooms`); clicks green "Shortlist" action button on room card (`button-action-shortlist-{room.id}`); verifies modal mount with default RESULTS tab; asserts all 4 statistical summary cards: Total Applicants (6), Shortlisted (3, 50%), Under Review (3), and Active Strategy ("Score ≥ 80%"); asserts footer text ("3 of 6 applicants shortlisted"). | ✅ **PASSED** | ~16.8s |
| **TC-US25-03** | `test_tc_us25_03_min_score_threshold_shortlisting` | Switches to Configure Rules tab (`tab-shortlist-criteria`); selects Minimum Score Threshold strategy (`card-strategy-min-score`); sets threshold to 85.0% (`input-shortlist-min-score`); saves criteria (`button-save-shortlist-criteria`); asserts automatic switch back to Results tab; verifies Alice (92.0), Bob (85.0), and Charlie (85.0) receive green "Shortlisted" badges (`badge-shortlisted-{id}`) and row highlights; verifies David (72.0) and unranked candidates receive "Under Review" badges with explicit reason ("Below minimum score threshold of 85.0%"). | ✅ **PASSED** | ~18.5s |
| **TC-US25-04** | `test_tc_us25_04_top_n_candidates_shortlisting` | Switches to Configure Rules tab; selects Top N Candidates strategy (`card-strategy-top-n`); clicks quick button for Top 3 (`quick-top-n-3`); saves and applies criteria; verifies exactly top 3 candidates are shortlisted (Rank #1 Alice, Rank #2 Bob, Rank #3 Charlie); verifies multi-tier tie-breaking preserves Bob at #2 (CV 90%) over Charlie at #3 (CV 80%); verifies Rank #4 David is Under Review with reason stating "Ranked #4, outside required top 3 quota". | ✅ **PASSED** | ~18.9s |
| **TC-US25-05** | `test_tc_us25_05_combined_strategy_and_boundary_tests` | Tests Combined Strategy (`card-strategy-combined`); configures Top 2 candidates meeting minimum score of 80.0%; saves criteria; asserts Alice (#1) and Bob (#2) are shortlisted; asserts Charlie (#3) with score 85.0% is not shortlisted and displays reason "exceeds top 2 quota"; verifies input boundaries (0% and 100%). | ✅ **PASSED** | ~19.6s |
| **TC-US25-06** | `test_tc_us25_06_instant_search_and_status_filtering` | Tests interactive results filters: verifies instant search input (`input-search-shortlist`) filters by candidate name ("Alice") down to 1 row; tests "⭐ Shortlisted Only" filter tab (`filter-shortlisted_only`) rendering strictly shortlisted candidates; tests "Under Review" filter tab (`filter-non_shortlisted`) rendering strictly non-shortlisted candidates; tests "All Candidates" (`filter-all`) restoring complete roster. | ✅ **PASSED** | ~24.2s |
| **TC-US25-07** | `test_tc_us25_07_disable_strategy_and_reevaluate_button` | Switches to Configure Rules tab; selects "Disabled (Manual Review)" (`card-strategy-none`); saves criteria; asserts all 6 applicants reset to "Under Review" status; asserts explanation states "Automatic shortlisting is disabled for this room"; asserts shortlisted counter drops to 0; tests "Re-evaluate" action button (`button-reevaluate-shortlist`), verifying loading spinner and toast notification. | ✅ **PASSED** | ~18.3s |
| **TC-US25-08** | `test_tc_us25_08_mobile_responsive_shortlist_modal` | Resizes viewport to mobile phone dimensions (375x812); scrolls and clicks room card Shortlist action button; verifies modal mounts and adapts within mobile viewport geometry without horizontal overflow (`modal.width <= window.innerWidth + 15`); verifies candidate cards, status badges, and tab controls remain legible and accessible. | ✅ **PASSED** | ~12.8s |

---

### B. Backend Unit Tests (`backend/apps/recruitment/tests/test_us25_shortlisting.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_configure_shortlist_criteria_min_score` | Verifies HR room owner can configure shortlisting by minimum score threshold via PATCH API. | ✅ **PASSED** |
| `test_configure_shortlist_criteria_top_n` | Verifies HR room owner can configure shortlisting by required candidate count (Top N) via PATCH API. | ✅ **PASSED** |
| `test_configure_shortlist_criteria_combined` | Verifies HR room owner can configure combined criteria (Top N + Min Score) via PATCH API. | ✅ **PASSED** |
| `test_validation_invalid_strategy` | Verifies unsupported shortlisting strategies return HTTP 400 Bad Request with clear error. | ✅ **PASSED** |
| `test_validation_min_score_out_of_range` | Verifies negative scores (<0) or scores >100 are rejected with clear error messages. | ✅ **PASSED** |
| `test_validation_top_n_invalid` | Verifies Top N counts of zero or negative are rejected with HTTP 400 Bad Request. | ✅ **PASSED** |
| `test_validation_missing_required_fields` | Verifies strategies missing their required parameters are rejected with explicit field errors. | ✅ **PASSED** |
| `test_automatic_shortlisting_min_score_logic` | Verifies candidates meeting `final_score >= min_score` are shortlisted and persisted in the database. | ✅ **PASSED** |
| `test_automatic_shortlisting_top_n_logic` | Verifies Top N ranked candidates are shortlisted based on deterministic score ranking. | ✅ **PASSED** |
| `test_automatic_shortlisting_combined_logic` | Verifies combined mode enforces minimum score threshold strictly within Top N quota. | ✅ **PASSED** |
| `test_disabled_strategy_resets_shortlist` | Verifies setting strategy to `NONE` resets `is_shortlisted` to False and clears timestamps. | ✅ **PASSED** |
| `test_shortlist_updates_on_criteria_patch` | Verifies updating criteria via API immediately re-evaluates all applicants and updates counts. | ✅ **PASSED** |
| `test_shortlist_updates_on_score_calculation` | Verifies batch score calculation in `scoring_service.py` triggers automatic shortlist re-evaluation. | ✅ **PASSED** |
| `test_get_shortlisted_applicants_endpoint` | Verifies `GET /api/recruitment/rooms/{id}/shortlisted-applicants/` returns full candidate evaluations. | ✅ **PASSED** |
| `test_shortlisted_applicants_access_control` | Verifies strict RBAC: unauthorized HR managers cannot view shortlists for rooms they do not own (HTTP 404). | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verification

### ✅ AC-1: Configurable Criteria (Minimum Score, Top N, Combined, or Disabled)
- **Verification:** HR can select among 4 distinct screening modes on the UI (`card-strategy-min-score`, `card-strategy-top-n`, `card-strategy-combined`, `card-strategy-none`). Minimum score threshold is configurable via range slider and numeric input (0-100%). Candidate count (Top N) is configurable via quick selection chips (Top 3, 5, 10, 15, 20) and custom input.
- **Evidence:** Verified in automated UI tests `TC-US25-03`, `TC-US25-04`, `TC-US25-05`, `TC-US25-07` and backend tests `test_configure_shortlist_criteria_*`.

### ✅ AC-2: Candidates Shortlisted Automatically with Deterministic Tie-Breaking
- **Verification:** Candidates are evaluated automatically according to active rules. When scores are equal, deterministic tie-breaking hierarchy is applied (`-final_score, -cv_score, -video_score, applied_at, id`). In `TC-US25-04`, Bob Builder (85.0%, CV 90%) was placed at Rank #2 ahead of Charlie Cloud (85.0%, CV 80%) at Rank #3. Unranked applicants with incomplete evaluations remain safely unshortlisted under review.
- **Evidence:** Verified in automated UI tests `TC-US25-03`, `TC-US25-04`, `TC-US25-05` and backend tests `test_automatic_shortlisting_*`.

### ✅ AC-3: Strict Criteria Input Validation with Clear Error Messages
- **Verification:** Validation rules in `shortlisting_service.py` and `RoomShortlistCriteriaSerializer` reject negative scores, scores exceeding 100%, non-positive Top N values, and missing parameters with clear, human-readable errors (e.g., `"Minimum score threshold must be between 0.0 and 100.0."`, `"Required candidate count (Top N) must be at least 1."`). Client-side checks in `ShortlistConfigModal.tsx` also alert the user before network submission.
- **Evidence:** Verified in backend tests `test_validation_invalid_strategy`, `test_validation_min_score_out_of_range`, `test_validation_top_n_invalid`, and `test_validation_missing_required_fields`.

### ✅ AC-4: Shortlist Status & Transparency Explanations Stored in Database
- **Verification:** Model `CandidateApplication` explicitly stores `is_shortlisted` (indexed boolean), `shortlist_reason` (descriptive string explanation), and `shortlisted_at` (audit timestamp). Every applicant card in the UI displays their exact criteria explanation (e.g., *"Met minimum score threshold of 85.0% (Score: 92.0%)."*, *"Ranked #4, outside required top 3 quota (Score: 72.0%)."*).
- **Evidence:** Verified in automated UI test `TC-US25-03`, `TC-US25-04`, and backend test `test_automatic_shortlisting_min_score_logic`.

### ✅ AC-5: Dynamic Re-evaluation on Criteria or Applicant Score Changes
- **Verification:** When criteria are updated via `PATCH /api/recruitment/rooms/{id}/shortlist-criteria/`, applicants are re-evaluated and persisted in real time without manual re-triggering. Additionally, when `calculate_room_applicant_scores` recalculates room applicant scores in `scoring_service.py`, `evaluate_room_shortlist` is automatically invoked, updating shortlist membership. The UI also includes an interactive "Re-evaluate" action button.
- **Evidence:** Verified in automated UI tests `TC-US25-03`, `TC-US25-07` and backend tests `test_shortlist_updates_on_criteria_patch` and `test_shortlist_updates_on_score_calculation`.

### ✅ AC-6: Shortlisted Candidates Clearly Highlighted to HR
- **Verification:** 
  - **HR Dashboard:** Dropdown selector `⭐ View Room Shortlist...` and hero banner button "Review Shortlist" provide direct access to room shortlist results.
  - **Recruitment Rooms List:** Green "⭐ Shortlist" action button on every room card and menu item.
  - **Modal Results View:** Highlighted green table rows (`bg-[#e2f0e9]/15`), star badges (`⭐ Shortlisted`), score pill breakdowns, and dedicated filter tabs (`⭐ Shortlisted Only`, `Under Review`, `All Candidates`).
- **Evidence:** Verified in automated UI tests `TC-US25-01`, `TC-US25-02`, and `TC-US25-06`.

---

## 4. UI Testing Evidence & Screenshots

All 8 screenshots were captured during live Selenium execution and are archived in `tests/reports/screenshots/`:

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us25_01_dashboard_shortlist_modal_mount.png`](screenshots/us25_01_dashboard_shortlist_modal_mount.png) | HR Dashboard Shortlist Trigger | Displays the dashboard quick selector dropdown and the resulting `ShortlistConfigModal` mount with room metadata. |
| [`us25_02_room_card_shortlist_modal_and_stats.png`](screenshots/us25_02_room_card_shortlist_modal_and_stats.png) | Room Card Action & Summary Metrics | Displays all 4 summary cards: Total Applicants (6), Shortlisted (3, 50%), Under Review (3), and Rule Strategy ("Score ≥ 80%"). |
| [`us25_03_min_score_threshold_results.png`](screenshots/us25_03_min_score_threshold_results.png) | Minimum Score Threshold Results (≥85%) | Displays green "Shortlisted" badges for Alice (92.0%), Bob (85.0%), Charlie (85.0%) and "Under Review" badge for David (72.0%) with clear reason. |
| [`us25_04_top_n_shortlisting_results.png`](screenshots/us25_04_top_n_shortlisting_results.png) | Top N Candidates Shortlist (Top 3) | Demonstrates exactly 3 candidates shortlisted according to multi-tier tie-breaking; Rank #4 candidate clearly marked outside quota. |
| [`us25_05_combined_strategy_and_boundaries.png`](screenshots/us25_05_combined_strategy_and_boundaries.png) | Combined Criteria (Top 2 meeting ≥80%) | Demonstrates Top 2 quota applied to candidates meeting threshold; Rank #3 Charlie marked Under Review due to quota limit. |
| [`us25_06_search_and_status_filtering.png`](screenshots/us25_06_search_and_status_filtering.png) | Search & Status Filter Toolbars | Shows instant search by candidate name and dedicated status filter tabs (`⭐ Shortlisted Only` vs `Under Review`). |
| [`us25_07_disabled_strategy_and_reevaluate.png`](screenshots/us25_07_disabled_strategy_and_reevaluate.png) | Disabled Strategy & Manual Review | Demonstrates clean reset of all applicants to "Under Review" when shortlisting is disabled, plus "Re-evaluate" button functionality. |
| [`us25_08_mobile_responsive_shortlist_modal.png`](screenshots/us25_08_mobile_responsive_shortlist_modal.png) | Mobile Viewport Responsiveness (375x812) | Demonstrates mobile responsive layout adaptation, table horizontal scrolling, and touch-friendly controls. |

---

## 5. Code Review Findings & Teammate Observations

During peer testing and architectural inspection of Jannatun Naeem Mona's code, the following observations and minor UX considerations were noted. **Per team instructions, these have not been modified in the codebase and are documented here for the developer's attention:**

### Finding 1: Specification Variation — Boolean Flag vs TextChoices Enum
- **Plan Reference:** Sprint 5 Plan (Section 4.1) specified:
  ```python
  class ShortlistStatus(models.TextChoices):
      PENDING = 'PENDING', 'Pending Review'
      SHORTLISTED = 'SHORTLISTED', 'Shortlisted by AI'
      NOT_SHORTLISTED = 'NOT_SHORTLISTED', 'Not Shortlisted'
  shortlist_status = models.CharField(choices=ShortlistStatus.choices, default=ShortlistStatus.PENDING)
  ```
- **Implementation:** Mona implemented:
  ```python
  is_shortlisted = models.BooleanField(default=False, db_index=True)
  shortlist_reason = models.CharField(max_length=255, blank=True, default="")
  shortlisted_at = models.DateTimeField(null=True, blank=True)
  ```
- **Analysis:** Mona's approach is clean, highly query-efficient (boolean indexing), and provides explicit audit fields (`shortlist_reason` and `shortlisted_at`). However, it collapses `PENDING` and `NOT_SHORTLISTED` into `is_shortlisted = False` (distinguished via `shortlist_reason`). If US-26 (HR Review) expects an explicit 3-state `shortlist_status` enum field, a mapping helper or migration alias may be considered in future sprints.

### Finding 2: Controlled Input UX Quirk in Top N Stepper
- **Location:** `frontend/src/components/recruitment/ShortlistConfigModal.tsx` (Line 527)
  ```tsx
  onChange={(e) => setTopN(Math.max(1, Number(e.target.value)))}
  ```
- **Symptom:** When a user selects all and backspaces to clear the input in order to type a new number, `e.target.value` is `""`. Since `Number("") === 0`, `Math.max(1, 0)` immediately sets `topN` to `1`. If the user then types `2`, the input displays `12` instead of `2`.
- **Recommendation:** Allow an empty string in local input state while typing, and clamp `Math.max(1, value)` on blur (`onBlur`) or form submission.

### Finding 3: Database Transaction Wrapping for High-Volume Rooms
- **Location:** `backend/apps/recruitment/services/shortlisting_service.py` (`evaluate_room_shortlist`)
- **Analysis:** `evaluate_room_shortlist` updates applicants in a standard loop with `app.save(update_fields=...)`. For enterprise rooms with hundreds of applicants, wrapping the evaluation loop in `with transaction.atomic():` and/or using `CandidateApplication.objects.bulk_update()` would improve throughput and provide transactional rollback protection in failure scenarios.

### Finding 4: UI Text Header Upper Case Assertion
- **Location:** `frontend/src/components/recruitment/ShortlistConfigModal.tsx`
- **Analysis:** Statistical card headers use Tailwind's `uppercase tracking-wider` class (e.g., `TOTAL APPLICANTS`, `UNDER REVIEW`). Automated tests must perform case-insensitive comparisons or match uppercase strings.

---

## 6. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit Tests:** 15/15 passed (`python manage.py test apps.recruitment.tests.test_us25_shortlisting`)
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors (`npm run build`)
- [x] **Automated Selenium UI Tests:** 8/8 test cases passed (`pytest tests/test_us25_automatic_shortlisting_ui.py`)
- [x] **Acceptance Criteria Verification:** AC-1 through AC-6 fully verified on the UI
- [x] **Multi-Strategy Coverage:** Minimum Score, Top N, Combined, and Disabled modes verified
- [x] **Deterministic Tie-Breaking:** Verified CV Match > Video Score > Timestamp tie-breaking hierarchy
- [x] **Code Quality & Aesthetics:** Matches CareerFlow design system (star badges, green highlight rows, stat cards)
- [x] **Cross-Testing Approval:** Signed off by MD. Hasanul Mobin (@hasanulmobin)

---

## 7. Peer Review Recommendation

> **Verdict:** 🟢 **TESTING PASSED & APPROVED**  
> **Signoff Reviewer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) (Project Manager & Cross-Tester)  
> **Author:** Jannatun Naeem Mona ([@jn-mona04](https://github.com/jn-mona04)) (Systems Analyst / BA)  
> **Target Branch:** `develop`  
> **Summary:** Jannatun Naeem Mona has completed an exceptional implementation of US-25 Automatic Candidate Shortlisting. The shortlisting engine is accurate, robust, and supports 4 configurable strategies (Min Score, Top N, Combined, and Disabled) with deterministic tie-breaking. The UI in `ShortlistConfigModal.tsx` is intuitive and polished, featuring real-time statistics, search and status filters, and transparent criteria explanations. All 15 backend unit tests and all 8 automated Selenium UI tests passed with a 100% success rate. The minor observations noted in Section 5 are non-blocking and have been documented for future refinement.
