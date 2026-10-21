# Sprint 5 UI Testing Report — Task US-26-T6

**Sprint:** Sprint 5 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Human Review)  
**Epic:** Epic 6: Applicant Scoring, Ranking & Shortlisting  
**User Story:** US-26: HR Review of AI Results & Human Decision Audit Trail  
**Task:** US-26-T6 (Peer UI Testing & Code Review for HR Review Flow)  
**Author / Developer:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Reviewer / UI Tester:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Tester / QA Engineer)  
**Source Branch:** `feat/us-26-hr-review-ai-results`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-21 / 2026-10-22  
**Test Framework:** Selenium WebDriver + pytest & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.3 | pytest 9.1.1 | selenium 4.48.0  
**Environment:** Localhost (Frontend: `http://127.0.0.1:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`145.0.7559.133`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us26_review_ui.py`) | 🟢 **PASSED** |
| **Backend Unit Tests** | **9 / 9 Passed (100%)** (`backend/apps/recruitment/tests/test_us26_hr_decision.py`) | 🟢 **PASSED** |
| **Frontend TypeScript Build** | **Built in 10.19s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified** | 🟢 **PASSED** |
| **Defects Caught & Documented** | **1** (Async modal header fallback text polling in test harness) | 🛠️ **RESOLVED** |
| **UI Test Suite Duration** | **101.69 seconds (~1m 41s)** | ⏱️ **OPTIMAL** |
| **Backend Unit Test Duration** | **31.29 seconds** | ⏱️ **FAST** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us26_review_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Duration |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US26-01** | `test_tc_us26_01_modal_mount_and_signals_display` | HR logs into `/hr/rooms`; opens Shortlist modal (`modal-shortlist-config`); clicks "Review" on candidate; verifies Candidate Review Modal mounts (`modal-candidate-review`); verifies candidate name, composite final score meter (`text-final-score`), CV score (`text-cv-score`), evaluation weights banner, and AI Advisory Suggestion badge (`badge-ai-recommendation`). Dismisses cleanly via close button. | ✅ **PASSED** | ~12.5s |
| **TC-US26-02** | `test_tc_us26_02_ai_advisory_disclaimer_prominence` | Validates prominent AI Advisory Disclaimer notice (`banner-ai-advisory-disclaimer`) rendered verbatim across modal body: *"AI-generated scores and shortlisting recommendations are advisory tools designed to support, not replace, human hiring decisions."* (AC#5). | ✅ **PASSED** | ~11.8s |
| **TC-US26-03** | `test_tc_us26_03_confirm_shortlist_decision_flow` | HR selects candidate; clicks "Confirm Shortlist" (`btn-decision-confirm`); provides optional audit notes in `input-decision-notes`; clicks "Save Decision" (`btn-submit-decision`); verifies reactive success alert banner (`alert-decision-success`); asserts DB audit log (`hr_decision="CONFIRMED"`, `hr_decided_by` set, `hr_decided_at` timestamp recorded, `is_shortlisted=True`). | ✅ **PASSED** | ~13.2s |
| **TC-US26-04** | `test_tc_us26_04_override_validation_mandatory_justification` | Selects candidate not recommended by AI; clicks "Override AI" (`btn-decision-override`); verifies warning badge `badge-override-required` appears; enters short notes (<5 characters, e.g. "No"); asserts "Save Decision" submit button is disabled and prevents invalid override without sufficient audit justification (AC#4). | ✅ **PASSED** | ~11.9s |
| **TC-US26-05** | `test_tc_us26_05_override_successful_ai_inversion` | Enters comprehensive justification notes (>= 5 chars); clicks "Save Decision"; asserts success notification banner; verifies database audit: `hr_decision="OVERRIDDEN"`, `is_shortlisted=True` (AI decision successfully inverted to shortlisted), reviewer email and full justification notes persisted. | ✅ **PASSED** | ~13.1s |
| **TC-US26-06** | `test_tc_us26_06_reject_and_hold_decision_recording` | Tests "Reject Candidate" (`btn-decision-reject`): submits with explanation, asserts `hr_decision="REJECTED"`, `is_shortlisted=False`; then tests "Put On Hold" (`btn-decision-hold`): asserts status transitions to `hr_decision="ON_HOLD"`. | ✅ **PASSED** | ~14.4s |
| **TC-US26-07** | `test_tc_us26_07_tab_switching_cv_skills_and_video_metrics` | Tests multi-tab inspection: clicks `tab-review-cv` to inspect Matched Skills pills (`skill-matched-0`) and Missing Skills; clicks `tab-review-video` to inspect Speech Score, Visual Presence, WPM, and AI executive summary; clicks `tab-review-overview` to view Human Decision Audit Trail section (`audit-current-decision`, `audit-decided-by`). | ✅ **PASSED** | ~12.2s |
| **TC-US26-08** | `test_tc_us26_08_modal_dismissal_and_parent_table_sync` | Clicks close button (`button-close-review-modal`); asserts review modal unmounts while preserving parent shortlist modal (`modal-shortlist-config`) state, allowing continuous evaluation of other applicants. | ✅ **PASSED** | ~12.5s |

---

### B. Backend Unit Tests (`backend/apps/recruitment/tests/test_us26_hr_decision.py`)

| Test Method Name | Description | Status | Duration |
| :--- | :--- | :---: | :---: |
| `test_get_candidate_review_data_success` | Verifies room owner can retrieve complete candidate review details with composite scores, CV summary, video metrics, and AI advisory notice. | ✅ **PASSED** | ~3.4s |
| `test_get_candidate_review_data_unauthorized` | Verifies non-room-owner HR manager is rejected with HTTP 403 Forbidden under lateral tenant isolation. | ✅ **PASSED** | ~3.2s |
| `test_record_decision_confirm_shortlist` | Verifies HR can record `CONFIRMED` decision, updating `is_shortlisted=True`, reviewer FK, timestamp, and notes. | ✅ **PASSED** | ~3.6s |
| `test_record_decision_override_requires_notes` | Verifies overriding AI recommendation without justification notes or notes < 5 characters is rejected with HTTP 400 Bad Request. | ✅ **PASSED** | ~3.3s |
| `test_record_decision_override_success` | Verifies valid override inverts shortlist status, sets `hr_decision=OVERRIDDEN`, and stores audit notes. | ✅ **PASSED** | ~3.5s |
| `test_record_decision_reject` | Verifies recording `REJECTED` decision clears `is_shortlisted=False` and persists decision audit trail. | ✅ **PASSED** | ~3.4s |
| `test_record_decision_on_hold` | Verifies recording `ON_HOLD` decision persists correctly without mutating shortlist status. | ✅ **PASSED** | ~3.3s |
| `test_decision_endpoint_permissions` | Verifies candidate and unauthenticated requests are blocked with HTTP 401/403. | ✅ **PASSED** | ~3.7s |
| `test_ai_advisory_disclaimer_present` | Verifies AI Advisory Disclaimer text is returned verbatim in API response serialization. | ✅ **PASSED** | ~3.8s |

---

## 3. Acceptance Criteria Verification

- ✅ **AC 1 — Candidate Review Modal UI & Signals Display:**  
  The `CandidateReviewModal` component mounts smoothly over the candidate list, presenting candidate profile headers, composite final score meter, CV score, video score, room weighting breakdown, and AI recommendation badge.
- ✅ **AC 2 — Authoritative Human Decision Actions:**  
  Provides 4 distinct human action buttons: Confirm Shortlist (`CONFIRMED`), Override AI (`OVERRIDDEN`), Reject Candidate (`REJECTED`), and Put On Hold (`ON_HOLD`).
- ✅ **AC 3 — Mandatory Justification on AI Override:**  
  The system strictly enforces a minimum 5-character justification note when overriding AI recommendations. Submitting with empty or insufficient notes is blocked on both frontend (disabled button & warning badge) and backend (HTTP 400 validation error).
- ✅ **AC 4 — Complete Database Audit Trail:**  
  Every human decision records `hr_decision`, `hr_decided_by` (foreign key to authenticating HR Manager), `hr_decided_at` (UTC timestamp), and `hr_decision_notes`. The modal displays the previous audit trail on subsequent reviews.
- ✅ **AC 5 — Prominent AI Advisory Disclaimer:**  
  A distinct amber warning banner displays the advisory disclaimer across all review screens: *"AI-generated scores and shortlisting recommendations are advisory tools designed to support, not replace, human hiring decisions."*
- ✅ **AC 6 — Strict RBAC & Tenant Isolation:**  
  Enforced via `IsApplicationRoomOwner` permission. Only the HR Manager who created the recruitment room can access candidate review details or record decisions. Student roles and other HR managers receive HTTP 403 Forbidden.

---

## 4. UI Testing Evidence & Screenshots

All 8 screenshots were captured during live Selenium execution and are saved in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us26_01_review_modal_mount.png`](screenshots/us26_01_review_modal_mount.png) | Review Modal Mount & Signals | Shows modal mount, candidate name, final composite score (88.5%), CV score (92.0%), weights (50% CV / 50% Video), and AI Advisory Shortlist badge. |
| [`us26_02_ai_advisory_disclaimer.png`](screenshots/us26_02_ai_advisory_disclaimer.png) | AI Advisory Disclaimer Notice | Shows prominent amber disclaimer banner emphasizing that AI recommendations assist rather than replace human judgment. |
| [`us26_03_confirm_shortlist.png`](screenshots/us26_03_confirm_shortlist.png) | Confirm Shortlist Flow | Demonstrates "Confirm Shortlist" selection, review notes input, and reactive success banner upon decision save. |
| [`us26_04_override_validation_error.png`](screenshots/us26_04_override_validation_error.png) | Override Validation Guard | Shows "Mandatory for Overrides" warning badge and disabled Save Decision button when justification note is < 5 characters. |
| [`us26_05_override_success_audit.png`](screenshots/us26_05_override_success_audit.png) | Successful AI Override | Shows successful submission of override with explanatory notes, inverting candidate status to shortlisted. |
| [`us26_06_reject_and_hold_decisions.png`](screenshots/us26_06_reject_and_hold_decisions.png) | Reject & On Hold Flows | Demonstrates recording Reject and On Hold decisions with corresponding audit state updates. |
| [`us26_07_cv_skills_and_video_tabs.png`](screenshots/us26_07_cv_skills_and_video_tabs.png) | Multi-Tab Signal Inspection | Demonstrates tab navigation to CV Skills match analysis, matched/missing skill pills, and video presentation metrics. |
| [`us26_08_modal_dismissal_and_table_sync.png`](screenshots/us26_08_modal_dismissal_and_table_sync.png) | Clean Dismissal & State Sync | Verifies review modal dismisses cleanly and returns HR to the parent shortlist candidate roster. |

---

## 5. Defects Identified & Resolved During Peer Review

### 🟢 Defect 1: Asynchronous Modal Header Fallback Race Condition in Test Harness
- **Symptom:** In automated UI tests, querying `[data-testid='heading-candidate-name']` immediately after modal mount intermittently returned the fallback placeholder `"Candidate Review"` instead of the applicant's name (`"Alice Candidate"`).
- **Root Cause:** When `CandidateReviewModal` mounts, `apiGetCandidateReviewDetail()` executes asynchronously. Before the promise resolves, the heading renders fallback text. Fast Selenium runners polled before the React state update completed.
- **Resolution:** Implemented `open_candidate_review_modal()` helper in `tests/test_us26_review_ui.py` utilizing `WebDriverWait` with `EC.text_to_be_present_in_element()` to deterministically synchronize on state hydration before making assertions.
- **Outcome:** All 8 UI tests pass with 100% determinism.

---

## 6. Definition of Done (DoD) Signoff Checklist

- [x] All 6 Acceptance Criteria from user story US-26 verified and satisfied.
- [x] Backend unit tests pass 100% (9 / 9 passed in `test_us26_hr_decision.py`).
- [x] Automated Selenium UI tests pass 100% (8 / 8 passed in `test_us26_review_ui.py`).
- [x] Frontend TypeScript builds cleanly with 0 errors (`npm run build`).
- [x] AI advisory disclaimer is verbatim and visible across review views.
- [x] Mandatory justification notes for override are strictly enforced on both frontend and backend.
- [x] Audit trail fields (`hr_decision`, `hr_decided_by`, `hr_decided_at`, `hr_decision_notes`) persist and display accurately.
- [x] RBAC and lateral tenant isolation verified.
- [x] Visual evidence screenshots captured and archived in `tests/reports/screenshots/`.

---

## 7. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR MERGE**  
> 
> MD. Hasanul Mobin's implementation of **US-26: HR Review of AI Results & Human Decision Audit Trail** meets all architectural, functional, security, and UI/UX standards. The implementation cleanly empowers human recruiters to maintain authoritative oversight over AI recommendations with full auditability.
> 
> The pull request for branch `feat/us-26-hr-review-ai-results` into `develop` is officially **APPROVED**.

**Peer Reviewer:** Farhana Tahsin Bonny (@tahsinbonnie98)  
**Role:** Tester / QA Engineer  
**Date:** 2026-10-22
