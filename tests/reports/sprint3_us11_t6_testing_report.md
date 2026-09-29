# Sprint 3 UI Testing Report — Task US-11-T6
**Sprint:** Sprint 3 (Presentation AI)  
**User Story:** US-11: Video Upload & Recording  
**Task:** US-11-T6 (UI Testing for upload & recording)  
**Tester / Developer:** MD. Jubair Bin Hasan (Software Developer)  
**Date:** 2026-09-29  
**Framework:** Selenium WebDriver + pytest  
**Platform:** Windows 11 | Python 3.14.0 | pytest 9.1.1  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Test Cases** | **4** |
| **Passed** | **4 (100%)** |
| **Failed** | **0 (0%)** |
| **Execution Duration** | **22.60 seconds** |
| **Status** | 🟢 **PASSED & VERIFIED** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status |
| :--- | :--- | :--- | :---: |
| **TC-US11-T6-01** | `test_tc_us11_t6_01_navigation_and_ui_layout` | Candidate navigates from dashboard/sidebar to Presentation Studio (`/student/presentation`); verifies Webcam Recording & File Upload tabs, 250MB upload capacity banner, and FFmpeg auto-compression indicator badge. | ✅ **PASSED** |
| **TC-US11-T6-02** | `test_tc_us11_t6_02_upload_valid_mp4_video` | Candidate uploads valid MP4 video (`sample_pitch.mp4`) via the upload dropzone; verifies progress indicator, video persistence, and active card rendering with status `READY FOR ANALYSIS`. | ✅ **PASSED** |
| **TC-US11-T6-03** | `test_tc_us11_t6_03_reupload_take_replacement` | Candidate uploads a second take (`sample_take.webm`); verifies new take becomes the active video and previous take is deactivated (`is_active=False`) and archived in Presentation Take History. | ✅ **PASSED** |
| **TC-US11-T6-04** | `test_tc_us11_t6_04_unsupported_format_client_rejection` | Candidate attempts to select an unsupported file format; verifies client-side validation triggers error banner (`[data-testid='upload-error-banner']`) and prevents upload submission. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verified

- ✅ **Navigation & Studio Layout:** The Presentation Studio loads cleanly under `/student/presentation` and `/student/practice`. Both "Record Webcam" and "Upload File" tabs are rendered with interactive tab switching.
- ✅ **High-Capacity 250MB Upload Banner:** Clear informational callout informs candidates of the **250MB maximum file size** (supporting high-resolution phone/webcam videos up to 3 minutes) alongside the FFmpeg auto-compression indicator badge.
- ✅ **Valid Video File Ingestion:** Uploading `.mp4` and `.webm` files completes successfully, updating the Active Presentation Video card with metadata (filename, duration, status, and raw vs compressed file size).
- ✅ **Take Replacement & History Archival:** When a candidate records or uploads a new take, the previous take is automatically marked inactive and pushed into the "Presentation Take History" list with individual preview links and delete actions.
- ✅ **Client-Side File Validation:** Attempting to select invalid formats (e.g. `.txt`, `.pdf`) immediately displays a user-friendly error banner without crashing or triggering server 500 errors.
- ✅ **Database & Audit Isolation:** Tests confirmed that `PresentationVideo` records are isolated by student account, and upload events are logged in `DataAccessLog` for security compliance (US-36).

---

## 4. Test Environment & Artifacts

- **Test File:** [`tests/test_us11_video_upload_recording.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/test_us11_video_upload_recording.py)
- **Fixtures Used:** 
  - [`tests/fixtures/video/sample_pitch.mp4`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/fixtures/video/sample_pitch.mp4)
  - [`tests/fixtures/video/sample_take.webm`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/fixtures/video/sample_take.webm)
- **Report Location:** [`tests/reports/sprint3_us11_t6_testing_report.md`](file:///d:/Study/3.2/CSE-314/CareerFlow/tests/reports/sprint3_us11_t6_testing_report.md)
