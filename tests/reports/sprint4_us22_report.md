# Sprint 4 UI & Unit Testing Report — Task US-22-T6

**Sprint:** Sprint 4 (Recruitment Rooms & Candidate Submission)  
**User Story:** US-22: Applicant Application Submission  
**Task:** US-22-T6 (Peer Testing & Code Review for Applicant Application Submission Flow)  
**Peer Tester / Reviewer:** MD. Hasanul Mobin (@hasanulmobin1) (Project Manager & Peer Tester)  
**Developer:** Farhana Tahsin Bonny (@tahsinbonnie98) (Tester / QA Engineer)  
**Date:** 2026-10-15  
**Framework:** Selenium WebDriver + pytest & Django REST Framework APITestCase  
**Platform:** Windows 11 | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Backend Unit Tests** | **4 / 4 Passed (100%)** (`backend/apps/recruitment/tests/test_us22_submission.py`) |
| **Total Automated UI Test Cases** | **6** (`tests/test_us22_candidate_submission_ui.py`) |
| **UI Suite Status** | **6 / 6 Passed (100%)** |
| **Defects Caught & Documented** | **2** (Unapplied database migration `0004_candidateapplication`, missing `pytest-django` runtime dependency) |
| **Backend Test Duration** | **8.68 seconds** |
| **UI Test Suite Duration** | **69.86 seconds** |
| **Automated Suite Status** | 🟢 **PASSED & VERIFIED** |
| **Overall Recommendation** | 🟢 **APPROVED FOR MERGE INTO `develop`** |

---

## 2. Test Execution Matrix

### A. Backend Unit Tests (`apps/recruitment/tests/test_us22_submission.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_valid_submission` | Verifies multipart form submission creates a Student user, candidate CV, presentation video, records candidate application with status `COMPLETED`, and auto-initiates both the CV extraction and presentation scoring pipelines. | ✅ **PASSED** |
| `test_missing_fields` | Verifies negative scenario where required files (CV / video) are omitted; asserts HTTP 400 Bad Request with descriptive error response payload. | ✅ **PASSED** |
| `test_inactive_link_submission` | Validates that submissions against an inactive or deactivated recruitment room link are rejected with HTTP 410 Gone. | ✅ **PASSED** |
| `test_duplicate_submission` | Asserts that duplicate submissions from the same candidate email to the same recruitment room are rejected with HTTP 400 Bad Request ("already submitted"). | ✅ **PASSED** |

### B. Automated UI Tests (`tests/test_us22_candidate_submission_ui.py`)

| Test Case ID | Test Method Name | Description | Status |
| :--- | :--- | :--- | :---: |
| **TC-US22-01** | `test_tc_us22_01_public_application_page_mount_and_details` | Unauthenticated applicant navigates to `/apply/:token`; asserts page mounts without login prompt; verifies company name, job title, department, seniority level, required skills list, and evaluation formula weights (CV% vs Video%). | ✅ **PASSED** |
| **TC-US22-02** | `test_tc_us22_02_form_validation_and_required_fields` | Applicant inspects the submission form; verifies required input attributes on full name, email, CV upload, and video presentation; attempts submission without files and asserts submission is blocked without confirmation card. | ✅ **PASSED** |
| **TC-US22-03** | `test_tc_us22_03_file_upload_selection_and_feedback` | Applicant selects a valid PDF CV (`valid_sample.pdf`) and an MP4 video clip (`sample_pitch.mp4`); asserts the dropzones dynamically update with file icons, filenames, and computed sizes in MB. | ✅ **PASSED** |
| **TC-US22-04** | `test_tc_us22_04_e2e_successful_candidate_submission` | End-to-end submission flow: candidate enters name, email, uploads files, and clicks submit; verifies button loading state ("Submitting Application..."), mounts green confirmation card ("Application Received"), and verifies database records in `User`, `CandidateCV`, `PresentationVideo`, and `CandidateApplication`. | ✅ **PASSED** |
| **TC-US22-05** | `test_tc_us22_05_duplicate_submission_prevention` | The same applicant attempts a second submission to the same recruitment room; asserts API rejection ("already submitted") and verifies in database that duplicate applications are prevented. | ✅ **PASSED** |
| **TC-US22-06** | `test_tc_us22_06_inactive_room_candidate_access_blocked` | Applicant accesses deactivated token URL; verifies application error card renders with status `LINK_DEACTIVATED` / HTTP 410, displaying clear guidance and preventing candidate form submission. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verified

- ✅ **AC 1 — Public Unauthenticated Access:** Candidates access `/apply/:token` freely without login, viewing company name, job description, requirements, skills tags, and evaluation scoring weights.
- ✅ **AC 2 — Multipart Submission Ingestion:** Implemented `POST /api/recruitment/apply/<token>/submit/` supporting multipart/form-data with resume document (`.pdf`, `.docx`) and presentation video (`.mp4`, `.webm`, `.mov`).
- ✅ **AC 3 — Automatic Association with RecruitmentRoom:** Submissions automatically link the created student profile, CV, and video to the correct `RecruitmentRoom` via the cryptographic `share_token`.
- ✅ **AC 4 — File Validation & Dynamic Feedback:** Dropzone displays responsive file information upon selection (name, MB size) and validates file attachments before sending.
- ✅ **AC 5 — Incomplete Submission Rejection:** Incomplete applications lacking mandatory candidate details or required files return HTTP 400 Bad Request with informative feedback.
- ✅ **AC 6 — Confirmation Screen & Pipeline Triggering:** Successful submission displays a dedicated confirmation card informing the applicant that their CV extraction (`CVExtractionPipeline`) and video presentation analysis (`PipelineManager.run_pipeline`) have been initiated.
- ✅ **AC 7 — Duplicate Submission Guard:** Enforces single application per room per candidate (`unique_together = ('room', 'candidate')`), blocking repeat submissions with a clear alert.
- ✅ **AC 8 — Inactive Link Protection:** Access to deactivated or expired links renders an HTTP 410 Gone error page, blocking unauthorized application submissions.

---

## 4. Defects Caught & Handled During QA

During peer review and automated testing, 2 environment/runtime considerations were identified and addressed:

### 🟢 Defect 1: Unapplied Migration `0004_candidateapplication` (Database)
- **Description:** Branch `feat/us-22-candidate-submission` introduced migration `0004_candidateapplication.py`. In local testing environments, running the application without migrating caused database table missing errors on `careerflow_candidate_applications`.
- **Resolution:** Executed `python backend/manage.py migrate recruitment`. Validated that `CandidateApplication` table and unique constraints were created.

### 🟢 Defect 2: Missing `pytest-django` Dependency for Pytest Runners (Test Environment)
- **Description:** The developer's backend unit test file (`test_us22_submission.py`) used `@pytest.mark.django_db` and pytest fixtures (`db`, `client`). In environments where `pytest-django` was not installed, pytest threw `fixture 'db' not found` errors during standalone test execution.
- **Resolution:** Installed `pytest-django==4.14.0` in the environment (`python -m pip install pytest-django`). Verified that all 4 unit tests pass cleanly (4/4 passed).

---

## 5. Test Evidence & Screenshots

All automated Selenium test evidence has been captured and archived under `tests/reports/screenshots/`:

| Scenario | Screenshot Filename | Description |
| :--- | :--- | :--- |
| **TC-01** | [`us22_01_public_application_page.png`](screenshots/us22_01_public_application_page.png) | Public job opening details, skills chips, and scoring weights card |
| **TC-02** | [`us22_02_form_validation.png`](screenshots/us22_02_form_validation.png) | Form validation and required fields blocking incomplete submissions |
| **TC-03** | [`us22_03_file_selection_feedback.png`](screenshots/us22_03_file_selection_feedback.png) | Dynamic dropzone feedback with uploaded CV and Video filenames & sizes |
| **TC-04** | [`us22_04_application_submitted_confirmation.png`](screenshots/us22_04_application_submitted_confirmation.png) | Post-submission confirmation screen with automated AI pipeline notice |
| **TC-05** | [`us22_05_duplicate_submission_rejected.png`](screenshots/us22_05_duplicate_submission_rejected.png) | Rejection alert when the same candidate attempts duplicate submission |
| **TC-06** | [`us22_06_inactive_room_blocked.png`](screenshots/us22_06_inactive_room_blocked.png) | HTTP 410 error screen blocking submission on deactivated room links |

---

## 6. Test Environment & Artifacts

- **Backend Unit Tests:** [`backend/apps/recruitment/tests/test_us22_submission.py`](file:///e:/sdeproject/CareerFlow/backend/apps/recruitment/tests/test_us22_submission.py) (4/4 passed)
- **Automated UI Test Suite:** [`tests/test_us22_candidate_submission_ui.py`](file:///e:/sdeproject/CareerFlow/tests/test_us22_candidate_submission_ui.py) (6/6 passed)
- **Markdown Report Location:** [`tests/reports/sprint4_us22_report.md`](file:///e:/sdeproject/CareerFlow/tests/reports/sprint4_us22_report.md)

---

## 7. Final Recommendation

🟢 **APPROVED FOR MERGE INTO `develop`**  
The implementation of US-22 by Farhana Tahsin Bonny (@tahsinbonnie98) satisfies all functional, architectural, and security requirements. All 4 backend unit tests pass, and all 6 automated Selenium UI scenarios pass with zero regressions. The feature is verified and approved for squash-and-merge into `develop`.
