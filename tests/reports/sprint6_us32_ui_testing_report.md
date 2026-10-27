# Sprint 6 UI Testing & Peer Review Report — Task US-32-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Agency Management)  
**Epic:** Epic 7: Recruitment Agency Management  
**User Story:** US-32: Forward Shortlisted Candidate Profiles to Client Companies  
**Task:** US-32-T6 (Dedicated Peer UI Testing, Access Control Verification & Automated Selenium Test Suite)  
**Author / Peer UI Tester:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Lead Developer & Peer Tester)  
**Developer Under Review:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Source Branch:** `feat/us-32-forward-shortlist-client`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-27  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.3 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `fahad`)  
**Browser:** Headless (`Firefox 0.37.1` / `Chrome Headless`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **10 / 10 Passed (100%)** ([tests/test_us32_forward_shortlist_ui.py](file:///f:/CareerFlow/tests/test_us32_forward_shortlist_ui.py)) in 374.82s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **10 / 10 Passed (100%)** (`apps.recruitment.tests.test_us32_forward_shortlist`) in 65.93s | 🟢 **PASSED** |
| **Frontend Production Build** | **Vite build succeeds with 0 errors** (`npm run build`, 2,402 modules) in 24.17s | 🟢 **PASSED** |
| **Database Migrations** | **Migration 0008 & 0009 applied cleanly** (`python backend/manage.py migrate`) | 🟢 **VERIFIED** |
| **Commit `6796207` Fixes** | **`data-testid` alignments & cross-client guard verified** | 🟢 **VERIFIED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 through AC#6) fully covered by test suite** | 🟢 **VERIFIED** |
| **Code Review Policy** | **Zero modifications to Mobin's code; clean peer isolation; zero git push** | 📌 **ADHERED** |
| **Overall Recommendation** | **ALL 10 UI TESTS & 10 BACKEND TESTS PASS — OFFICIALLY VERIFIED & APPROVED** | 🟢 **APPROVED** |

---

## 2. Acceptance Criteria Verification Matrix

| AC ID | Description | Automated UI Test Case | Status |
| :--- | :--- | :--- | :---: |
| **AC#1** | **Candidate Selection for Forwarding (US-32-T3):** Multi-select checkboxes (`checkbox-candidate-{id}`), bulk toggle (`checkbox-select-all-shortlisted`), and floating action bar (`bar-forward-selection`) with dynamic count. | `test_tc_us32_01_candidate_selection_and_forward_bar_visibility`, `test_tc_us32_02_select_all_shortlisted_toggle` | 🟢 **VERIFIED** |
| **AC#2** | **Strict Shortlist Enforcement (US-32-T1, US-32-T2):** Only candidates with `is_shortlisted=True` can be selected or forwarded. Non-shortlisted candidates have disabled checkboxes and no row action. Backend returns HTTP 400 Bad Request if unshortlisted applicant is submitted. | `test_tc_us32_01_candidate_selection_and_forward_bar_visibility`, `test_tc_us32_04_single_candidate_row_forward_trigger` | 🟢 **VERIFIED** |
| **AC#3** | **Client Selection & Cross-Client Guard (US-32-T1, Commit `6796207`):** Client company auto-assigned and locked when candidates share one client. Cross-client batch submissions detected with alert (`alert-cross-client-error`), disabled submit button, and candidate-level client display. | `test_tc_us32_03_forward_modal_launch_and_form_prefill`, `test_tc_us32_08_cross_client_selection_ui_guard` | 🟢 **VERIFIED** |
| **AC#4** | **Delivery Dossier & Modal Workflow (US-32-T4):** Modal `modal-forward-candidates` displays candidate snapshot preview (CV/Video/Final score, category), agency cover note (`input-forward-notes`), and dispatches HTML dossier email template (`forwarded_shortlist.html`). | `test_tc_us32_03_forward_modal_launch_and_form_prefill`, `test_tc_us32_05_forward_submission_success_and_badge_update`, `test_tc_us32_06_bulk_forward_multi_candidates` | 🟢 **VERIFIED** |
| **AC#5** | **Forward History & Status Badges (US-32-T5):** Applications updated with `is_forwarded=True` and `forwarded_at`. Pipeline UI displays `badge-forwarded` status badge. `CandidateForwardRecord` audit record saved in database with `dossier_data` snapshot. | `test_tc_us32_05_forward_submission_success_and_badge_update`, `test_tc_us32_06_bulk_forward_multi_candidates` | 🟢 **VERIFIED** |
| **AC#6** | **Multi-Tenant Isolation & RBAC Protection (US-32-T2):** Agency A cannot forward or view candidates belonging to Agency B. Student and unauthenticated visitors blocked from `/agency/pipeline`. | `test_tc_us32_09_multi_tenant_isolation_boundary`, `test_tc_us32_10_rbac_protection_student_and_unauthenticated` | 🟢 **VERIFIED** |

---

## 3. Automated Selenium UI Test Suite Details (`tests/test_us32_forward_shortlist_ui.py`)

A comprehensive test suite containing 10 automated test cases has been authored and verified at [tests/test_us32_forward_shortlist_ui.py](file:///f:/CareerFlow/tests/test_us32_forward_shortlist_ui.py):

| Test Case ID | Test Method Name | Description | Acceptance Criteria | Execution Time | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **TC-US32-01** | `test_tc_us32_01_candidate_selection_and_forward_bar_visibility` | Tests shortlisted candidate checkbox selection (`checkbox-candidate-{id}`) and disabled non-shortlisted checkbox. Verifies floating forward bar `[data-testid='bar-forward-selection']` mounts with "1 Shortlisted candidate selected". Tests "Clear selection" button. | **AC#1, AC#2** | 35.12s | 🟢 **PASSED** |
| **TC-US32-02** | `test_tc_us32_02_select_all_shortlisted_toggle` | Tests select-all shortlisted toggle `[data-testid='checkbox-select-all-shortlisted']`. Verifies all visible shortlisted candidates are checked, count shows "2", and second click deselects all. | **AC#1** | 33.40s | 🟢 **PASSED** |
| **TC-US32-03** | `test_tc_us32_03_forward_modal_launch_and_form_prefill` | Tests forward modal mount `[data-testid='modal-forward-candidates']`. Verifies client dropdown is locked to target client, recipient email/name are auto-populated, candidate score preview renders, and cover note is populated via `input-forward-notes`. | **AC#3, AC#4** | 38.25s | 🟢 **PASSED** |
| **TC-US32-04** | `test_tc_us32_04_single_candidate_row_forward_trigger` | Tests individual row action button `[data-testid='button-forward-row-{id}']`. Verifies presence on shortlisted rows and absence on non-shortlisted rows. Tests modal launch for single candidate. | **AC#1, AC#2** | 35.19s | 🟢 **PASSED** |
| **TC-US32-05** | `test_tc_us32_05_forward_submission_success_and_badge_update` | Tests forward form submission `[data-testid='button-submit-forward']`. Verifies modal dismissal, row status badge `[data-testid='badge-forwarded']`, and database persistence (`is_forwarded=True`, `CandidateForwardRecord`). | **AC#4, AC#5** | 39.81s | 🟢 **PASSED** |
| **TC-US32-06** | `test_tc_us32_06_bulk_forward_multi_candidates` | Tests bulk multi-candidate forward workflow. Verifies multi-candidate dossier preview in modal, bulk submission, and simultaneous badge updates across all forwarded candidate rows. | **AC#1, AC#4, AC#5** | 37.94s | 🟢 **PASSED** |
| **TC-US32-07** | `test_tc_us32_07_validation_empty_recipient_email` | Tests client recipient email validation. Verifies clearing `input-recipient-email` triggers validation prevent submission. | **AC#4** | 36.45s | 🟢 **PASSED** |
| **TC-US32-08** | `test_tc_us32_08_cross_client_selection_ui_guard` | **Verifies Mobin's commit `6796207` cross-client guard.** When candidates from 2 different clients are selected: displays `[data-testid='alert-cross-client-error']`, disables target client select `[data-testid='select-forward-client']`, disables submit button `[data-testid='button-submit-forward']`, and previews client names. | **AC#3** | 39.20s | 🟢 **PASSED** |
| **TC-US32-09** | `test_tc_us32_09_multi_tenant_isolation_boundary` | Tests agency isolation boundary. Verifies Agency 1 cannot view or forward Agency 2's candidate applications or clients. | **AC#6** | 38.60s | 🟢 **PASSED** |
| **TC-US32-10** | `test_tc_us32_10_rbac_protection_student_and_unauthenticated` | Tests strict RBAC protection. Verifies Student role and unauthenticated visitors cannot access `/agency/pipeline`. | **AC#6** | 37.35s | 🟢 **PASSED** |

---

## 4. Backend Unit & Integration Tests (`apps.recruitment.tests.test_us32_forward_shortlist`)

All 10 backend tests authored by Mobin pass cleanly in 65.93s (`python backend/manage.py test apps.recruitment.tests.test_us32_forward_shortlist`):

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_forward_single_shortlisted_candidate_success` | Forward single shortlisted candidate with email dispatch (AC#1, AC#4) | ✅ **PASSED** |
| `test_forward_multiple_shortlisted_candidates_success` | Batch forward multiple shortlisted candidates to client (AC#1, AC#5) | ✅ **PASSED** |
| `test_forward_unshortlisted_candidate_rejected_with_400` | Strict validation rejecting non-shortlisted candidates (AC#2) | ✅ **PASSED** |
| `test_forward_candidates_to_another_agency_client_forbidden` | Multi-tenant security guard preventing cross-agency forwarding (AC#6) | ✅ **PASSED** |
| `test_forward_candidates_to_deactivated_client_rejected` | Guard preventing forward to inactive client company | ✅ **PASSED** |
| `test_forward_candidate_belonging_to_different_client_rejected` | Guard ensuring applications match the selected target client | ✅ **PASSED** |
| `test_forward_history_endpoint_lists_records` | Audit log retrieval via `GET /api/recruitment/agency/forward-history/` (AC#5) | ✅ **PASSED** |
| `test_forward_history_multi_tenant_isolation` | Multi-tenant isolation ensuring Agency A cannot see Agency B forward history | ✅ **PASSED** |
| `test_email_dispatch_failure_marks_status_failed` | Graceful degradation marking record FAILED if SMTP fails without crash | ✅ **PASSED** |
| `test_rbac_unauthorized_users_blocked` | RBAC test: 401 for unauthenticated, 403 for Student & HR Manager | ✅ **PASSED** |

---

## 5. Peer Review Findings & Mobin's Commit `6796207` Resolution

During peer review of Mobin's branch (`feat/us-32-forward-shortlist-client`), 3 selector discrepancies and 1 cross-client guard improvement were reported to Mobin. Mobin pushed commit `6796207`, and our automated test suite verified that **all items are now resolved**:

### ✅ Resolved Item 1: Candidate Selection Checkbox Selector
- **Prior State:** Implemented as `data-testid="checkbox-select-applicant-{app.id}"`.
- **Commit `6796207` Update:** Aligned to `data-testid="checkbox-candidate-${app.id}"` in `frontend/src/pages/AgencyApplicantsPipelinePage.tsx`.
- **Verification:** Verified by `TC-US32-01` and `TC-US32-02`. 🟢 **RESOLVED**

### ✅ Resolved Item 2: Forward Notes Textarea Selector
- **Prior State:** Implemented as `data-testid="textarea-forward-notes"`.
- **Commit `6796207` Update:** Aligned to `data-testid="input-forward-notes"` in `frontend/src/components/recruitment/ForwardCandidatesModal.tsx`.
- **Verification:** Verified by `TC-US32-03`, `TC-US32-05`, and `TC-US32-06`. 🟢 **RESOLVED**

### ✅ Resolved Item 3: Forwarded Status Badge Selector
- **Prior State:** Implemented only with dynamic ID `data-testid="badge-forwarded-${app.id}"`.
- **Commit `6796207` Update:** Added `data-testid="badge-forwarded"` with `id="badge-forwarded-${app.id}"` in `frontend/src/pages/AgencyApplicantsPipelinePage.tsx`.
- **Verification:** Verified by `TC-US32-05` and `TC-US32-06`. 🟢 **RESOLVED**

### ✅ Verified New Feature: Cross-Client Selection UI Guard
- **Commit `6796207` Implementation:** 
  - Added `isCrossClient` check in `ForwardCandidatesModal.tsx`.
  - Renders alert `[data-testid="alert-cross-client-error"]` when selected candidates belong to different client companies.
  - Disables client select dropdown (`data-testid="select-forward-client"`).
  - Disables submit button (`data-testid="button-submit-forward"`) with explanatory tooltip.
  - Renders client company name on each candidate badge in the modal preview list.
- **Verification:** Verified by dedicated test `TC-US32-08` (`test_tc_us32_08_cross_client_selection_ui_guard`). 🟢 **VERIFIED & PASSED**

---

## 6. Screenshot Evidence Gallery

All 10 automated test screenshots were captured, validated, and archived under [tests/reports/screenshots/](file:///f:/CareerFlow/tests/reports/screenshots/):

| Evidence ID | Description | File Path |
| :--- | :--- | :--- |
| **US32-01** | Candidate selection checkbox (`checkbox-candidate-{id}`) & floating forward action bar | [us32_01_candidate_selection_bar.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_01_candidate_selection_bar.png) |
| **US32-02** | Select-all shortlisted toggle with 2 candidates selected | [us32_02_select_all_toggle.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_02_select_all_toggle.png) |
| **US32-03** | Forward Candidates Modal pre-filled with client contact & candidate dossier (`input-forward-notes`) | [us32_03_forward_modal_prefilled.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_03_forward_modal_prefilled.png) |
| **US32-04** | Single-candidate row-level quick forward modal trigger | [us32_04_single_row_forward_modal.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_04_single_row_forward_modal.png) |
| **US32-05** | Forwarded badge (`badge-forwarded`) on pipeline row and database persistence state | [us32_05_forwarded_badge_and_state.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_05_forwarded_badge_and_state.png) |
| **US32-06** | Bulk multi-candidate forward success and synchronized badge updates | [us32_06_bulk_forward_success.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_06_bulk_forward_success.png) |
| **US32-07** | Client recipient email validation preventing empty submission | [us32_07_validation_recipient_email.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_07_validation_recipient_email.png) |
| **US32-08** | Cross-client validation guard alert (`alert-cross-client-error`), disabled submit & client name preview | [us32_08_cross_client_validation_alert.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_08_cross_client_validation_alert.png) |
| **US32-09** | Multi-tenant isolation boundary between Agency 1 and Agency 2 | [us32_09_multi_tenant_isolation.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_09_multi_tenant_isolation.png) |
| **US32-10** | Strict RBAC protection redirecting student and unauthenticated visitors | [us32_10_rbac_protection.png](file:///f:/CareerFlow/tests/reports/screenshots/us32_10_rbac_protection.png) |

---

## 7. Peer Review Verdict & Sign-Off

- **Development Tasks US-32-T1 to US-32-T5 & US-32-T7:** Completed by Hasanul Mobin. Verified and working cleanly.
- **Testing Task US-32-T6:** Completed by Farhana Tahsin Bonny. Automated Selenium test suite authored (10 test cases) and 100% passing.
- **Commit `6796207` Verification:** All requested selector alignments and the cross-client validation UI guard are verified and passing.
- **Build & Quality:** Vite production build passes with 0 errors (`npm run build`). All 10 backend tests pass with 0 regressions.
- **Code Integrity Policy:** **Zero edits to Mobin's files; zero git push performed.**
- **Recommendation:** **READY FOR MERGE INTO `develop`**.

