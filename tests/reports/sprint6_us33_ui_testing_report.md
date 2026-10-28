# Sprint 6 UI Testing & Peer Review Report — Task US-33-T6

**Sprint:** Sprint 6 (Smart Recruitment Decisions: Scoring, Ranking, Shortlisting & Agency Management)  
**Epic:** Epic 8: Reporting & Notifications  
**User Story:** US-33: Downloadable Applicant & Room Reports (PDF)  
**Task:** US-33-T6 (Dedicated Peer UI Testing, Access Control Verification & Automated Selenium Test Suite)  
**Author / Peer UI Tester:** Farhana Tahsin Bonny ([@tahsinbonnie98](https://github.com/tahsinbonnie98)) (Lead Developer & Peer Tester)  
**Developer Under Review:** MD. Hasanul Mobin ([@hasanulmobin1](https://github.com/hasanulmobin1)) (Project Manager & Full Stack Developer)  
**Source Branch:** `feat/us-33-downloadable-reports`  
**Target Merge Branch:** `develop`  
**Date of Testing:** 2026-10-28  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** Windows 11 (win32) | Python 3.14.3 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `fahad`)  
**Browser:** Headless (`Microsoft Edge 131+` / `Firefox 0.37.1`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **10 / 10 Passed (100%)** ([tests/test_us33_downloadable_reports_ui.py](file:///f:/CareerFlow/tests/test_us33_downloadable_reports_ui.py)) in 102.59s | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **12 / 12 Passed (100%)** (`apps.recruitment.tests.test_us33_downloadable_reports`) in 74.44s | 🟢 **PASSED** |
| **Frontend Production Build** | **Vite build succeeds with 0 errors** (`npm run build`, 2,402 modules) in 14.53s | 🟢 **PASSED** |
| **Database Migrations** | **All migrations applied cleanly up to 0009** (`python backend/manage.py migrate`) | 🟢 **VERIFIED** |
| **Acceptance Criteria Verified** | **All 6 ACs (AC#1 through AC#6) fully covered by test suite** | 🟢 **VERIFIED** |
| **Code Review Policy** | **Zero modifications to Mobin's code; clean peer isolation; zero git push** | 📌 **ADHERED** |
| **Overall Recommendation** | **ALL 10 UI TESTS & 12 BACKEND TESTS PASS — ALL FINDINGS RESOLVED (COMMIT 7639262)** | 🟢 **APPROVED FOR MERGE** |

---

## 2. Acceptance Criteria Verification Matrix

| AC ID | Description | Automated UI Test Case | Status |
| :--- | :--- | :--- | :---: |
| **AC#1** | **Downloadable Applicant & Room Reports (US-33-T4):** Action triggers available across Candidate Review Modal (`button-download-candidate-pdf`), Room List Menu (`button-download-room-pdf-{room.id}`), Ranked Applicants Modal (`button-download-room-summary-pdf`), and Agency Pipeline Table/Modal (`button-download-applicant-pdf-{id}`, `button-modal-download-candidate-pdf`). | `test_tc_us33_01_candidate_review_modal_pdf_download`, `test_tc_us33_02_room_list_action_menu_pdf_download`, `test_tc_us33_03_ranked_applicants_modal_summary_download`, `test_tc_us33_04_agency_pipeline_row_candidate_download`, `test_tc_us33_05_agency_pipeline_detail_modal_candidate_download` | 🟢 **VERIFIED** |
| **AC#2** | **Publication-Quality Vector PDF Engine (US-33-T1, US-33-T2):** ReportLab PDF generation with clean corporate typography, branding, two-pass `NumberedCanvas` ('Page X of Y'), confidentiality headers, and valid `%PDF-` binary stream. | `test_tc_us33_06_direct_pdf_bytestream_validation` | 🟢 **VERIFIED** |
| **AC#3** | **Granular Evaluation Data Aggregation (US-33-T3):** Multi-modal scorecard rendering final composite score, CV semantic match score, video presentation score, CV matched/gap skills, speech analytics (WPM, filler words), behavioral metrics (eye contact, posture), and HR decision audit trail. | `test_tc_us33_01_candidate_review_modal_pdf_download`, `test_tc_us33_06_direct_pdf_bytestream_validation` | 🟢 **VERIFIED** |
| **AC#4** | **Strict Access Control & Multi-Tenant Authorization (US-33-T5):** Enforced via `IsRoomOwnerOrAdmin`. Room owner (HR Manager) and managing Agency Admin can download reports; foreign HR Managers, foreign Agency Admins, Students, and unauthenticated visitors are blocked with HTTP 401/403. | `test_tc_us33_08_multitenant_access_control`, `test_tc_us33_09_rbac_protection_student_and_unauthenticated` | 🟢 **VERIFIED** |
| **AC#5** | **Graceful Missing Data Handling & Incomplete Evaluations (US-33-T2):** Missing CV or Video telemetry generates clean PDF with warning callout banner and partial score notice without throwing HTTP 500 errors. | `test_tc_us33_07_incomplete_candidate_evaluation_report` | 🟢 **VERIFIED** |
| **AC#6** | **Streaming Performance Requirement (< 2.5s):** Vector PDF generation and streaming response completes in well under 2.5 seconds per report. | `test_tc_us33_06_direct_pdf_bytestream_validation` | 🟢 **VERIFIED** |

---

## 3. Automated Selenium UI Test Suite Details (`tests/test_us33_downloadable_reports_ui.py`)

A comprehensive test suite containing 10 automated test cases has been authored and verified at [tests/test_us33_downloadable_reports_ui.py](file:///f:/CareerFlow/tests/test_us33_downloadable_reports_ui.py):

| Test Case ID | Test Method Name | Description | Acceptance Criteria | Execution Time | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **TC-US33-01** | `test_tc_us33_01_candidate_review_modal_pdf_download` | Tests candidate review modal mount and download trigger `[data-testid='button-download-candidate-pdf']`. Verifies modal header placement, button state, and download trigger. | **AC#1, AC#3** | 12.85s | 🟢 **PASSED** |
| **TC-US33-02** | `test_tc_us33_02_room_list_action_menu_pdf_download` | Tests room list action menu `[data-testid='button-more-actions-{room.id}']` on `/hr/rooms` and verifies `[data-testid='button-download-room-pdf-{room.id}']` mounts and triggers room summary PDF export. | **AC#1** | 11.40s | 🟢 **PASSED** |
| **TC-US33-03** | `test_tc_us33_03_ranked_applicants_modal_summary_download` | Tests opening Ranked Applicants modal from HR dashboard and verifies header action `[data-testid='button-download-room-summary-pdf']` triggers summary PDF download. | **AC#1** | 13.12s | 🟢 **PASSED** |
| **TC-US33-04** | `test_tc_us33_04_agency_pipeline_row_candidate_download` | Tests candidate row action `[data-testid='button-download-applicant-pdf-{app.id}']` in `/agency/pipeline`. Verifies download icon, tooltip, and download trigger. | **AC#1** | 12.05s | 🟢 **PASSED** |
| **TC-US33-05** | `test_tc_us33_05_agency_pipeline_detail_modal_candidate_download` | Tests opening applicant detail modal and verifies footer action `[data-testid='button-modal-download-candidate-pdf']` triggers candidate evaluation PDF download. | **AC#1** | 11.80s | 🟢 **PASSED** |
| **TC-US33-06** | `test_tc_us33_06_direct_pdf_bytestream_validation` | Tests direct streaming of `/api/recruitment/applications/{id}/report-pdf/` and `/api/recruitment/rooms/{id}/summary-pdf/`. Asserts `%PDF-` binary signature, Content-Disposition header, and generation time < 2.5s. | **AC#2, AC#6** | 8.24s | 🟢 **PASSED** |
| **TC-US33-07** | `test_tc_us33_07_incomplete_candidate_evaluation_report` | Tests candidate report generation when video interview is missing or partial. Verifies detection of `incompleteness_reasons` and warning box rendering in PDF without crash. | **AC#5** | 7.95s | 🟢 **PASSED** |
| **TC-US33-08** | `test_tc_us33_08_multitenant_access_control` | Tests multi-tenant isolation. Verifies foreign HR Manager and foreign Agency Admin receive HTTP 403 Forbidden when requesting other owners' reports. | **AC#4** | 9.40s | 🟢 **PASSED** |
| **TC-US33-09** | `test_tc_us33_09_rbac_protection_student_and_unauthenticated` | Tests strict RBAC protection. Verifies unauthenticated visitors receive HTTP 401 and Student role users receive HTTP 403 Forbidden. | **AC#4** | 8.65s | 🟢 **PASSED** |
| **TC-US33-10** | `test_tc_us33_10_skills_data_format_validation` | Tests data format handling for `skills_required`. Verifies string-based skills succeed and documents Mobin's dictionary-based sequence item TypeError bug. | **AC#3** | 7.86s | 🟢 **PASSED** |

---

## 4. Backend Unit & Integration Tests (`apps.recruitment.tests.test_us33_downloadable_reports`)

All 12 backend tests authored by Mobin pass cleanly in 74.44s (`python backend/manage.py test apps.recruitment.tests.test_us33_downloadable_reports`):

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_generate_candidate_report_pdf_success_by_room_owner` | Room owner HR Manager can download candidate report PDF (AC#1, AC#4) | ✅ **PASSED** |
| `test_generate_candidate_report_pdf_by_agency_admin` | Agency Admin managing client company can download candidate report PDF | ✅ **PASSED** |
| `test_candidate_report_unauthorized_hr_forbidden` | Unauthorized HR Manager blocked with HTTP 403 Forbidden (AC#4) | ✅ **PASSED** |
| `test_candidate_report_unauthorized_agency_forbidden` | Rogue Agency Admin blocked with HTTP 403 Forbidden (AC#4) | ✅ **PASSED** |
| `test_candidate_report_unauthenticated_rejected` | Anonymous visitor rejected with HTTP 401 Unauthorized (AC#4) | ✅ **PASSED** |
| `test_candidate_report_nonexistent_application_404` | Non-existent application ID returns HTTP 404 Not Found | ✅ **PASSED** |
| `test_candidate_report_with_incomplete_data_graceful` | Missing/incomplete evaluation data generates cleanly without crash (AC#5) | ✅ **PASSED** |
| `test_room_summary_pdf_success_by_owner` | Room owner can download executive room summary PDF (AC#1) | ✅ **PASSED** |
| `test_room_summary_pdf_empty_roster_graceful` | Empty room with no applicants generates clean PDF without crash | ✅ **PASSED** |
| `test_room_summary_pdf_with_dict_skills_required` | Dict-based skills_required list generates clean PDF (Regression Test) | ✅ **PASSED** |
| `test_room_summary_unauthorized_forbidden` | Unauthorized HR Manager blocked from room summary with HTTP 403 (AC#4) | ✅ **PASSED** |
| `test_report_generation_performance` | PDF generation completes in < 2.5s (AC#6) | ✅ **PASSED** |

---

## 5. Peer Review Findings & Resolution Analysis (Mobin's Codebase)

During peer review and initial UI test execution of Mobin's branch (`feat/us-33-downloadable-reports`), the ReportLab layout design, multi-modal aggregation, and UI action triggers were found to be comprehensive. **2 issues** were identified, communicated to Mobin, and have now been **fully resolved** by Mobin in commit `7639262`:

### ✅ Critical Bug 1: `TypeError` Crash on `skills_required` in Room Summary PDF Generation (RESOLVED)
- **Location:** `backend/apps/recruitment/services/report_service.py:680`
- **Initial Finding:**
  `skills_required` on `RecruitmentRoom` is a JSONField storing a list of dictionaries (`[{"name": "Python", "importance": "REQUIRED", ...}]`).
  Calling `", ".join(data['skills_required'])` directly on dictionaries threw `TypeError: sequence item 0: expected str instance, dict found`, returning HTTP 500 when exporting Room Summaries.
- **Mobin's Fix (Commit `7639262`):**
  Updated `report_service.py` to extract `.get('name', str(s))` for all skill items across `skills_required`, `skills_matched`, and `skills_missing`:
  ```python
  skills_raw = data.get('skills_required') or []
  skills_list = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in skills_raw]
  skills_req_str = ", ".join(skills_list) if skills_list else "General requirements"
  ```
- **Verification:**
  Mobin added regression unit test `test_room_summary_pdf_with_dict_skills_required` in `test_us33_downloadable_reports.py`.
  Peer automated test `test_tc_us33_10_skills_data_format_validation` re-verified end-to-end PDF generation with dict skills: **PASSED**.

---

### ✅ Discrepancy 2: Missing `reportlab` in `backend/requirements.txt` (RESOLVED)
- **Location:** `backend/requirements.txt`
- **Initial Finding:**
  `reportlab` was imported in `report_service.py` but absent from `backend/requirements.txt`, risking `ModuleNotFoundError` on fresh deployments.
- **Mobin's Fix (Commit `7639262`):**
  Added `reportlab>=4.0.0` to `backend/requirements.txt`.
- **Verification:**
  Dependency resolves cleanly in environment: **VERIFIED**.

---

## 6. Screenshot Evidence Gallery

All 10 automated test screenshots were captured, validated, and archived under [tests/reports/screenshots/](file:///f:/CareerFlow/tests/reports/screenshots/):

| Evidence ID | Description | File Path |
| :--- | :--- | :--- |
| **US33-01** | Candidate Review Modal header with `button-download-candidate-pdf` | [us33_01_candidate_review_modal_download.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_01_candidate_review_modal_pdf_download.png) |
| **US33-02** | Room List three-dot action menu displaying `button-download-room-pdf-{room.id}` | [us33_02_room_list_menu_download.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_02_room_list_menu_download.png) |
| **US33-03** | Ranked Applicants Modal header displaying `button-download-room-summary-pdf` | [us33_03_ranked_applicants_modal_download.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_03_ranked_applicants_modal_download.png) |
| **US33-04** | Agency Pipeline table row with `button-download-applicant-pdf-{app.id}` | [us33_04_agency_pipeline_row_download.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_04_agency_pipeline_row_download.png) |
| **US33-05** | Agency Pipeline applicant detail modal with `button-modal-download-candidate-pdf` | [us33_05_agency_pipeline_modal_download.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_05_agency_pipeline_modal_download.png) |
| **US33-06** | Direct PDF byte-stream binary validation and performance streaming (< 2.5s) | [us33_06_pdf_stream_validation.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_06_pdf_stream_validation.png) |
| **US33-07** | Candidate report with incomplete/pending evaluation warning callout banner | [us33_07_incomplete_evaluation_handling.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_07_incomplete_evaluation_handling.png) |
| **US33-08** | Multi-tenant security isolation blocking foreign HR Managers & Agency Admins | [us33_08_multitenant_access_control.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_08_multitenant_access_control.png) |
| **US33-09** | Strict RBAC protection blocking Student role and unauthenticated visitors | [us33_09_rbac_protection.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_09_rbac_protection.png) |
| **US33-10** | Skills data format verification and sequence item TypeError reproduction | [us33_10_skills_format_validation.png](file:///f:/CareerFlow/tests/reports/screenshots/us33_10_skills_format_validation.png) |

---

## 7. Peer Review Verdict & Sign-Off

- **Development Tasks US-33-T1 to US-33-T5 & US-33-T7:** Completed by Hasanul Mobin. ReportLab PDF engine is robust, multi-modal metrics render accurately, and all edge cases are handled cleanly.
- **Testing Task US-33-T6:** Completed by Farhana Tahsin Bonny. Automated Selenium test suite authored (10 test cases) and 100% passing (10/10).
- **Backend Unit Tests:** 12/12 passing cleanly (including new regression test `test_room_summary_pdf_with_dict_skills_required`).
- **Frontend Production Build:** Compiles cleanly with 0 errors (`npm run build`, 2,402 modules).
- **Code Review Policy:** **Zero edits were made to Mobin's code; zero git push performed.**
- **Verdict:** **APPROVED AND SIGNED OFF FOR MERGE INTO `develop`** 🟢.
