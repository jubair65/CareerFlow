# Sprint 7 UI Testing Report — Task US-45-T6

**Sprint:** Sprint 7 (System Enhancements & Platform Maturity: Candidate Self-Service, Room Lifecycle Controls, Bulk Exports, Pipeline Notes, Ethical AI Consent & Automated Storage Retention)  
**Epic:** Epic 3: Recruitment & Room Lifecycle Management  
**User Story:** US-45: Recruitment Room Lifecycle & Expiration Management (DRAFT, OPEN, PAUSED, CLOSED states & application deadlines)  
**Task:** US-45-T6 (Dedicated Peer UI Selenium Automation Testing, Room Lifecycle Controls, Public Application Gatekeeper & Verification Report)  
**Author / Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222))  
**Reviewer / Dedicated Peer UI Tester:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) (Dedicated Peer UI Automation Tester & Reviewer)  
**Target Merge Branch:** `develop` (from `feat/us-45-room-lifecycle`)  
**Date of Testing:** 2026-11-01  
**Test Framework:** Selenium WebDriver (`selenium 4.49.0`) + pytest (`pytest 9.1.1`) & Django TestCase  
**Platform:** Windows 11 | Python 3.14.2 | pytest 9.1.1 | selenium 4.49.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Microsoft Edge Headless  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us45_room_lifecycle_ui.py`) | 🟢 **PASSED** |
| **Backend Unit & Isolation Tests** | **20 / 20 Passed (100%)** (`backend/apps/recruitment/tests/test_us45_room_lifecycle.py`) | 🟢 **PASSED** |
| **Full Recruitment Test Suite** | **34 / 34 Passed (100%)** (`apps.recruitment.tests`) | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 14.12s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified (100%)** | 🟢 **PASSED** |
| **Public Submission Gatekeeping** | **100% Verified** (HTTP 410 Gone gatekeeper for PAUSED, CLOSED, DRAFT, and expired rooms) | 🛡️ **SECURE** |
| **Urgency Countdown Banner** | **100% Verified** (Live timer countdown alert when < 24 hours remain until deadline) | ⏱️ **VERIFIED** |
| **UI Test Suite Duration** | **75.42 seconds** (8 comprehensive browser interaction scenarios) | ⚡ **OPTIMAL** |
| **Backend Unit Test Duration** | **30.38 seconds** | ⚡ **FAST** |
| **Visual Evidence Archive** | **8 High-Resolution Screenshots Captured** (`tests/reports/screenshots/`) | 📸 **ARCHIVED** |
| **Overall Recommendation** | **APPROVED FOR MERGE INTO `develop`** | 🚀 **READY** |

### Executive Overview & Verification Assessment
As part of Sprint 7 platform maturity and operational controls, User Story **US-45** implements full recruitment room lifecycle state machines and expiration deadline controls. Under **Task US-45-T6**, dedicated peer UI automation testing was conducted by **MD. Hasanul Mobin** ([@hasanulmobin](https://github.com/hasanulmobin)) on feature branch `feat/us-45-room-lifecycle` authored by **Nafisa Tabassum Maria** ([@Maria-07-222](https://github.com/Maria-07-222)).

The verification validated:
1. **Multi-State Lifecycle Engine (AC-2, AC-5):** Full support for 4 lifecycle states: `OPEN` (with `ACTIVE` alias for backward compatibility), `PAUSED`, `CLOSED`, and `DRAFT`. State transitions are handled cleanly via `PATCH /api/recruitment/rooms/{id}/status/` and reflected across color-coded UI badges (`room-status-${id}`).
2. **Interactive 5-Way HR Status Filters (`RoomList.tsx` - AC-6):** HR Managers can instantly filter room cards using filter pills (`filter-status-all`, `filter-status-open`, `filter-status-paused`, `filter-status-closed`, `filter-status-draft`) to isolate rooms in specific operational phases.
3. **Application Deadline Configuration Modal (AC-1):** The Quick Deadline Modal (`modal-set-deadline`) allows setting, updating, or clearing dates. Deadlines are persisted in MySQL (`application_deadline`), formatted cleanly in local timezone on room cards (`room-deadline-value-${id}`), and displayed with active or expired badges.
4. **Manual Room Reopening (AC-5):** Paused or closed rooms can be manually reopened via dropdown actions (`button-reopen-room-${id}`) or toggle buttons (`button-toggle-status-${id}`), restoring `is_open=True` and `is_accepting_applications=True`.
5. **Public Applicant Portal Live Urgency Banner (`PublicApplicationPage.tsx` - AC-1, AC-3):** When an open room has an application deadline less than 24 hours away, the public applicant page renders the live countdown urgency banner (`public-deadline-urgency-banner`), displaying the remaining hours/minutes in real-time.
6. **Robust Gatekeeping & Error Screen Resilience (AC-3, AC-4):** When candidates access a paused or expired room via `/apply/:token`, the backend gatekeeper (`validate_share_token`) rejects the request with HTTP 410 Gone and structured error codes (`ROOM_PAUSED`, `DEADLINE_PASSED`). The frontend renders a dedicated error screen (`card-link-error`), completely preventing unauthorized candidate submissions.
7. **Deadline Deletion / Infinite Window (AC-1):** Clicking *"Clear Deadline"* in the modal resets `application_deadline` to `null` in the database, immediately displaying *"No deadline set (Open indefinitely)"* on the room card.

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us45_room_lifecycle_ui.py`)

| Test Case ID | Test Method Name | Scenario & Verification Scope | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-45-01** | `test_tc45_01_hr_status_filter_pills` | Authenticates HR Manager; visits `/hr/rooms`; toggles `filter-status-open`, `filter-status-paused`, `filter-status-closed`, `filter-status-draft`, and `filter-status-all`; validates accurate room card filtering in DOM for each state. (AC-6) | 🟢 **PASSED** | 13.2s |
| **TC-45-02** | `test_tc45_02_set_and_update_room_deadline` | Opens Quick Deadline Modal (`button-set-deadline-${id}`); sets future datetime (`YYYY-MM-DDTHH:mm`); clicks save; asserts modal closes, room card displays formatted deadline and active badge, and DB `application_deadline` updates. (AC-1) | 🟢 **PASSED** | 8.8s |
| **TC-45-03** | `test_tc45_03_pause_and_close_room` | In an active room, opens more actions menu (`button-more-actions-${id}`); clicks `button-pause-room-${id}`; asserts status badge updates to `PAUSED`; clicks `button-close-room-${id}`; asserts status badge updates to `CLOSED` and DB state matches. (AC-2, AC-3) | 🟢 **PASSED** | 7.9s |
| **TC-45-04** | `test_tc45_04_manual_reopening` | Locates a closed room; opens more actions dropdown; clicks `button-reopen-room-${id}`; verifies room badge transitions back to `OPEN` and room properties `is_open=True` and `is_accepting_applications=True`. (AC-5) | 🟢 **PASSED** | 7.4s |
| **TC-45-05** | `test_tc45_05_applicant_live_urgency_banner` | Creates open room with deadline 5.5 hours away; visits `/apply/{token}`; asserts `page-public-application` loads, `public-deadline-urgency-banner` displays *"Applications Close Soon"* with remaining countdown, and submit button is enabled. (AC-1, AC-3) | 🟢 **PASSED** | 8.1s |
| **TC-45-06** | `test_tc45_06_applicant_submission_blocked_paused_room` | Configures room in `PAUSED` state; visits public `/apply/{token}`; asserts gatekeeper returns HTTP 410, renders `card-link-error` with status badge `ROOM_PAUSED` (*"Applications Temporarily Paused"*), and direct API submission is blocked with 410 Gone. (AC-3) | 🟢 **PASSED** | 7.6s |
| **TC-45-07** | `test_tc45_07_applicant_submission_blocked_past_deadline` | Configures room with deadline in the past; visits `/apply/{token}`; asserts gatekeeper returns HTTP 410, renders `card-link-error` with status badge `DEADLINE_PASSED` (*"Application Deadline Has Passed"*), and direct API submission is blocked. (AC-4) | 🟢 **PASSED** | 7.7s |
| **TC-45-08** | `test_tc45_08_clear_deadline` | In room with configured deadline, opens Quick Deadline Modal; clicks `button-clear-deadline`; asserts modal closes, card text reverts to *"No deadline set (Open indefinitely)"*, and DB `application_deadline` is `null`. (AC-1) | 🟢 **PASSED** | 8.2s |

### B. Backend Unit Test Suite (`backend/apps/recruitment/tests/test_us45_room_lifecycle.py`)

| Test Class | Test Count | Scope | Result |
| :--- | :---: | :--- | :---: |
| `RecruitmentRoomLifecycleModelTests` | 5 | Validates 4 lifecycle status choices, `is_past_deadline` calculation, `is_open`, `is_accepting_applications`, and `check_deadline_and_auto_close()` auto-transitioning logic. | 🟢 **5 / 5 PASSED** |
| `RoomStatusUpdateAPITests` | 5 | Tests `PATCH /api/recruitment/rooms/{id}/status/` for valid state transitions (OPEN ↔ PAUSED ↔ CLOSED), invalid transitions, unauthenticated rejection, and cross-HR permission isolation. | 🟢 **5 / 5 PASSED** |
| `RoomDeadlineUpdateAPITests` | 4 | Tests `PATCH /api/recruitment/rooms/{id}/deadline/` for setting future ISO deadlines, clearing deadlines with `null`, past date rejection, and owner permission checks. | 🟢 **4 / 4 PASSED** |
| `RoomQuerySetStatusFilterAPITests` | 3 | Tests `GET /api/recruitment/rooms/?status=OPEN|PAUSED|CLOSED|DRAFT|ALL` query parameter filtering on the recruitment room ViewSet. | 🟢 **3 / 3 PASSED** |
| `PublicSubmissionGatekeeperTests` | 3 | Tests `validate_share_token` blocking candidate access and submissions for paused, closed, and expired rooms with HTTP 410 Gone and error codes. | 🟢 **3 / 3 PASSED** |
| **Total Backend Tests** | **20** | **Comprehensive model, API, query, and submission gatekeeping verification** | 🟢 **20 / 20 PASSED (100%)** |

---

## 3. Acceptance Criteria (AC) Verification Summary

| AC ID | Acceptance Criteria Description | Implementation Details | Verification Evidence | Status |
| :---: | :--- | :--- | :--- | :---: |
| **AC-1** | **Setting & Clearing Room Application Deadlines** | Model field `application_deadline = DateTimeField(null=True, blank=True)`, API `PATCH /api/recruitment/rooms/{id}/deadline/`, Quick Deadline Modal (`modal-set-deadline`), Clear Deadline control. | `test_tc45_02_set_and_update_room_deadline`<br>`test_tc45_08_clear_deadline`<br>Unit: `RoomDeadlineUpdateAPITests` | 🟢 **VERIFIED** |
| **AC-2** | **Room Status Transitions (DRAFT, OPEN, PAUSED, CLOSED)** | Model `Status` choices expanded with `DRAFT`, `OPEN`, `PAUSED`, `CLOSED` (and `ACTIVE` compatibility alias); API `PATCH /api/recruitment/rooms/{id}/status/`. | `test_tc45_03_pause_and_close_room`<br>Unit: `RoomStatusUpdateAPITests` | 🟢 **VERIFIED** |
| **AC-3** | **Applicant Submission Gating on Paused Rooms** | Backend `validate_share_token` returns `status_code=410` and `error_code="ROOM_PAUSED"`; public frontend displays dedicated error card `card-link-error`. | `test_tc45_06_applicant_submission_blocked_paused_room`<br>Unit: `PublicSubmissionGatekeeperTests` | 🟢 **VERIFIED** |
| **AC-4** | **Applicant Submission Gating Past Deadlines** | Helper `is_past_deadline` detects expired deadlines; gatekeeper returns HTTP 410 with `error_code="DEADLINE_PASSED"`; frontend displays expired error screen. | `test_tc45_07_applicant_submission_blocked_past_deadline`<br>Unit: `PublicSubmissionGatekeeperTests` | 🟢 **VERIFIED** |
| **AC-5** | **Manual Room Reopening** | HR can transition closed or paused rooms back to `OPEN` via more actions menu or toggle button, restoring public application acceptance. | `test_tc45_04_manual_reopening`<br>Unit: `RoomStatusUpdateAPITests` | 🟢 **VERIFIED** |
| **AC-6** | **Room Status Filtering in HR Dashboard** | Status pills (`filter-status-all`, `filter-status-open`, `filter-status-paused`, `filter-status-closed`, `filter-status-draft`) in `RoomList.tsx` and query filtering `?status=` in backend. | `test_tc45_01_hr_status_filter_pills`<br>Unit: `RoomQuerySetStatusFilterAPITests` | 🟢 **VERIFIED** |

---

## 4. Architectural Findings & Developer Advisory Note

### Dedicated Error Card (`card-link-error`) vs Inline Form Notice (`alert-room-paused`)
During UI automation testing of applicant gatekeeping scenarios (**TC-45-05** through **TC-45-07**), an interesting architectural pattern in Maria's implementation was observed:

1. **Gatekeeper Design (High Security):**
   - In `backend/apps/recruitment/tokens.py` (`validate_share_token`), when a room is in `PAUSED`, `CLOSED`, `DRAFT`, or `DEADLINE_PASSED` state, the validation function immediately returns `is_valid=False, status_code=410`.
   - In `PublicRoomDetailView.get`, this causes the room fetch API `GET /api/recruitment/public/rooms/{token}/` to respond with `HTTP 410 Gone`.
   - In `PublicApplicationPage.tsx` (lines 152–215), the Axios rejection triggers the early-return block rendering `<div data-testid="card-link-error">` with status badges (*"Status Code: ROOM_PAUSED"*, *"Status Code: DEADLINE_PASSED"*).
2. **Behavioral Impact:**
   - Because the dedicated error screen (`card-link-error`) mounts on initial page visit for inactive/expired rooms, the full application form containing `<div data-testid="alert-room-paused">` and `<button data-testid="button-submit-application">` is **intentionally not mounted** on initial load.
   - This is actually **more secure and user-friendly**, as candidates are completely prevented from typing or attempting to submit into a disabled form.
   - The inline banners (`alert-room-paused` and `alert-room-closed`) exist as in-page fallback indicators if a candidate had already loaded an active page before the room was paused or expired live.
3. **Recommendation for Developer:**
   - Keep this secure behavior intact! It provides defense-in-depth against unauthorized submissions.
   - In future test scenarios, peer reviewers should verify `card-link-error` with appropriate status copy when testing initial access to closed/paused rooms.

---

## 5. Visual Evidence Archive

The test suite generated 8 visual evidence screenshots saved in `CareerFlow/tests/reports/screenshots/`:

| Scenario ID | Screenshot Filename | Description |
| :---: | :--- | :--- |
| **TC-45-01** | `us45_01_status_filters.png` | HR rooms dashboard with 5-way status filter pills and status-filtered cards. |
| **TC-45-02** | `us45_02_set_deadline.png` | Room card with updated deadline datetime and green *Active* badge. |
| **TC-45-03** | `us45_03_pause_close_room.png` | More actions menu and room cards transitioned to *PAUSED* and *CLOSED*. |
| **TC-45-04** | `us45_04_manual_reopening.png` | Reopened room card restored to *OPEN* status badge. |
| **TC-45-05** | `us45_05_urgency_countdown.png` | Public applicant portal displaying live urgency banner with remaining countdown. |
| **TC-45-06** | `us45_06_applicant_paused_blocked.png` | Dedicated error card displaying *ROOM_PAUSED* and *"Applications Temporarily Paused"*. |
| **TC-45-07** | `us45_07_applicant_deadline_passed.png` | Dedicated error card displaying *DEADLINE_PASSED* and *"Application Deadline Has Passed"*. |
| **TC-45-08** | `us45_08_clear_deadline.png` | Room card reverted to *"No deadline set (Open indefinitely)"* after clearing. |

---

## 6. Peer Sign-Off & Recommendation

- **Functionality Verification:** 100% Verified (All 8 UI scenarios passed, 20/20 backend unit tests passed).
- **Code Quality:** Excellent modularity, proper database migrations (`0011_recruitmentroom_application_deadline_and_more.py`), and robust gatekeeper security.
- **Merge Sign-Off:** **APPROVED** for merge into `develop`.

