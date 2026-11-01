# Sprint 7 UI Testing Report — Task US-46-T6

**Sprint:** Sprint 7 (System Enhancements & Platform Maturity: Candidate Self-Service, Room Lifecycle Controls, Bulk Exports, Pipeline Notes, Ethical AI Consent & Automated Storage Retention)  
**Epic:** Epic 3: Recruitment & Room Lifecycle Management  
**User Story:** US-46: Bulk Applicant Data Export — CSV / Excel  
**Task:** US-46-T6 (Dedicated Peer UI Automation Testing, Export Data Triggers, File Integrity & Verification Report)  
**Author / Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222))  
**Reviewer / Dedicated Peer UI Tester:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) (Dedicated Peer UI Automation Tester & Reviewer)  
**Target Merge Branch:** `develop` (from `feat/us-46-bulk-applicant-export`)  
**Date of Testing:** 2026-11-01  
**Test Framework:** Selenium WebDriver (`selenium 4.49.0`) + pytest (`pytest 9.1.1`) & Django TestCase  
**Platform:** Windows 11 | Python 3.14.2 | pytest 9.1.1 | selenium 4.49.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Microsoft Edge Headless  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us46_bulk_export_ui.py`) | 🟢 **PASSED** |
| **Backend Unit & Integration Tests** | **12 / 12 Passed (100%)** (`backend/apps/recruitment/tests/test_us46_bulk_export.py`) | 🟢 **PASSED** |
| **Regression Test Suite** | **23 / 23 Passed (100%)** (`test_us24_ranking`, `test_us33_downloadable_reports`) | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 12.16s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified (100%)** | 🟢 **PASSED** |
| **CSV Streaming & UTF-8 BOM** | **100% Verified** (O(1) memory generator, `\ufeff` prefix for MS Excel compatibility) | 📊 **VERIFIED** |
| **Formatted Excel (.xlsx) Generation** | **100% Verified** (OpenPyXL, #277254 styled header, zebra striping, auto-fit columns) | 📑 **VERIFIED** |
| **Filter & Search Preservation** | **100% Verified** (Preserves `shortlisted`, `min_score`, `search`, `ordering`) | 🔍 **VERIFIED** |
| **RBAC & Multi-Tenant Isolation** | **100% Verified** (HTTP 401 unauth, HTTP 403 students and rogue cross-company HR) | 🛡️ **SECURE** |
| **UI Test Suite Duration** | **88.89 seconds** (8 comprehensive browser interaction scenarios) | ⚡ **OPTIMAL** |
| **Visual Evidence Archive** | **8 High-Resolution Screenshots Captured** (`tests/reports/screenshots/`) | 📸 **ARCHIVED** |
| **Overall Recommendation** | **APPROVED FOR MERGE INTO `develop`** | 🚀 **READY** |

### Executive Overview & Verification Assessment
As part of Sprint 7 platform maturity and recruiter productivity features, User Story **US-46** introduces bulk applicant evaluation data export capabilities into downloadable CSV and styled Excel (`.xlsx`) files. Under **Task US-46-T6**, dedicated peer UI automation testing was conducted by **MD. Hasanul Mobin** ([@hasanulmobin](https://github.com/hasanulmobin)) on feature branch `feat/us-46-bulk-applicant-export` authored by **Nafisa Tabassum Maria** ([@Maria-07-222](https://github.com/Maria-07-222)).

The verification validated:
1. **Interactive Export Dropdown UI (`RankedApplicantsModal.tsx` - AC-1):** In the HR applicant rankings leaderboard modal (`modal-ranked-applicants`), clicking the *"Export Data"* dropdown trigger (`button-export-applicants`) displays two styled download options: *"Export as CSV"* (`button-export-csv`) and *"Export as Excel (.xlsx)"* (`button-export-excel`). Clicking triggers client-side blob download utilities with dynamic progress toasts (`toast-message`).
2. **CSV Streaming Engine & UTF-8 BOM (`export_service.py` - AC-4, AC-5):** The CSV export endpoint (`GET /api/recruitment/rooms/{id}/export/csv/`) generates a low-memory streaming response (`StreamingHttpResponse`) prepended with the standard UTF-8 Byte Order Mark (`\ufeff`). This prevents Microsoft Excel encoding corruptions when opening UTF-8 characters across varied locales.
3. **Styled Professional Excel Workbook (`generate_applicants_excel` - AC-1, AC-2):** The Excel generator constructs a multi-row structured workbook with CareerFlow header branding, deep emerald column headers (`#277254`), alternating white and soft grey zebra striping (`#F9FAFB`), auto-computed column widths, and proper cell formatting.
4. **Mandatory Candidate Attribute Columns (AC-2):** Both CSV and Excel export outputs contain all 9 required evaluation dimensions:
   - Rank
   - Candidate Name
   - Email
   - CV Match Score (%)
   - Video Presentation Score (%)
   - Final Weighted Score (%)
   - Shortlisted Status (`Yes` / `No`)
   - Application Status
   - Applied Date (`YYYY-MM-DD HH:MM`)
5. **Filter & Search Preservation (AC-3):** Active UI leaderboard filters seamlessly propagate into the export parameters:
   - Activating *"Shortlisted Only"* (`button-filter-shortlisted-only`) queries `?shortlisted=true`, filtering the exported rows down to shortlisted candidates only.
   - Searching for a specific applicant via `input-ranked-search` propagates `?search=<query>` into the download URL, exporting only matching applicants.
6. **Delimited Character Escaping (AC-4):** Names containing embedded commas, double quotes, or honorifics (e.g. `Dr. Sarah "Sally" O'Connor, Ph.D.`) are quoted according to RFC 4180 without column splitting or parsing corruption.
7. **Zero-State Graceful Handling (AC-1, AC-5):** Recruitment rooms with 0 applicant submissions return HTTP 200 with table headers intact and 0 candidate data rows without raising unhandled exceptions.
8. **Strict RBAC & Cross-Tenant Isolation (AC-6):** Only room owners and organization recruiters have access to applicant export endpoints. Unauthenticated requests return HTTP 401; student candidate tokens and unauthorized cross-company HR managers are rejected with HTTP 403 Forbidden.

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us46_bulk_export_ui.py`)

| Test Case ID | Test Method Name | Scenario & Verification Scope | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-46-01** | `test_tc46_01_export_dropdown_mount_and_options` | Authenticates HR Manager; navigates to `/hr/rooms`; opens Rankings modal (`button-action-ranking-{id}`); clicks *"Export Data"* dropdown (`button-export-applicants`); asserts CSV and Excel export options mount cleanly in DOM. (AC-1) | 🟢 **PASSED** | 10.7s |
| **TC-46-02** | `test_tc46_02_export_csv_download_and_content_verification` | Triggers CSV export from UI; asserts HTTP 200 response; verifies UTF-8 BOM (`\ufeff`); validates all 9 column headers; asserts applicant records match leaderboard data with formatted score values. (AC-1, AC-2, AC-4) | 🟢 **PASSED** | 9.4s |
| **TC-46-03** | `test_tc46_03_export_excel_download_and_structure_verification` | Triggers Excel export from UI; asserts HTTP 200 binary response; validates OpenPyXL parsing; confirms sheet title, CareerFlow brand header, table header row 5, #277254 background fill, and candidate row count. (AC-1, AC-2) | 🟢 **PASSED** | 9.2s |
| **TC-46-04** | `test_tc46_04_filter_preservation_shortlisted_only` | Toggles *"Shortlisted Only"* filter pill in modal (`button-filter-shortlisted-only`); validates UI badge; executes export with `?shortlisted=true`; asserts only shortlisted applicants are included in output. (AC-3) | 🟢 **PASSED** | 9.8s |
| **TC-46-05** | `test_tc46_05_filter_preservation_search_query` | Enters candidate query into `input-ranked-search` and triggers Enter; asserts leaderboard filters; verifies export endpoint preserves `?search=` parameter and exports only matching records. (AC-3) | 🟢 **PASSED** | 11.2s |
| **TC-46-06** | `test_tc46_06_csv_escaping_commas_and_quotes` | Configures candidate with complex name containing commas and quotes (`Dr. Sarah "Sally" O'Connor, Ph.D.`); verifies RFC 4180 CSV escaping, ensuring quotes are escaped and columns do not shift. (AC-4) | 🟢 **PASSED** | 8.8s |
| **TC-46-07** | `test_tc46_07_empty_room_export_graceful_handling` | Targets an empty room with 0 applicants; verifies CSV and Excel export endpoints return HTTP 200, outputting column headers and 0 data rows gracefully without crashing. (AC-1, AC-5) | 🟢 **PASSED** | 8.1s |
| **TC-46-08** | `test_tc46_08_rbac_cross_tenant_isolation` | Tests RBAC protections: asserts unauthenticated requests return 401; student candidate requests return 403; unauthorized cross-company HR returns 403; verifies room is completely isolated in UI. (AC-6) | 🟢 **PASSED** | 12.6s |

### B. Backend Unit & Integration Tests (`backend/apps/recruitment/tests/test_us46_bulk_export.py`)

| Test Class | Test Count | Scope | Result |
| :--- | :---: | :--- | :---: |
| `ApplicantDataExportAPITests` | 12 | Tests CSV streaming, UTF-8 BOM, column completeness, Excel workbook styles, cell fills, filter preservation (`shortlisted`, `min_score`, `search`), comma/quote escaping, empty rooms, unauthenticated 401, candidate 403, and cross-HR 403. | 🟢 **12 / 12 PASSED** |
| **Total Backend Tests** | **12** | **Full export engine, streaming generator, styling, and RBAC coverage** | 🟢 **12 / 12 PASSED (100%)** |

### C. Regression Test Suites

| Test Suite | Test Count | Focus Area | Result |
| :--- | :---: | :--- | :---: |
| `apps.recruitment.tests.test_us24_ranking` | 13 | Core Applicant Ranking Engine & Score Computation | 🟢 **13 / 13 PASSED** |
| `apps.recruitment.tests.test_us33_downloadable_reports` | 10 | PDF / Summary Report Generation Infrastructure | 🟢 **10 / 10 PASSED** |

---

## 3. Acceptance Criteria (AC) Verification Summary

| AC ID | Acceptance Criteria Description | Implementation Details | Verification Evidence | Status |
| :---: | :--- | :--- | :--- | :---: |
| **AC-1** | **CSV and Styled Excel (.xlsx) Export Options** | Dropdown button `button-export-applicants` with child options `button-export-csv` and `button-export-excel`. Backend endpoints `/export/csv/` and `/export/excel/`. | `test_tc46_01_export_dropdown_mount_and_options`<br>`test_tc46_02_export_csv_download_and_content_verification`<br>`test_tc46_03_export_excel_download_and_structure_verification` | 🟢 **VERIFIED** |
| **AC-2** | **Mandatory Candidate Evaluation Dimensions** | 9 columns: Rank, Candidate Name, Email, CV Match Score (%), Video Presentation Score (%), Final Weighted Score (%), Shortlisted Status, Application Status, Applied Date. | `test_tc46_02_export_csv_download_and_content_verification`<br>`test_tc46_03_export_excel_download_and_structure_verification` | 🟢 **VERIFIED** |
| **AC-3** | **Preservation of Active Filter & Sorting Parameters** | Supports `?shortlisted=true`, `?min_score=<int>`, `?search=<str>`, `?ordering=<field>` in export endpoints. Frontend dynamically maps active modal state to query params. | `test_tc46_04_filter_preservation_shortlisted_only`<br>`test_tc46_05_filter_preservation_search_query` | 🟢 **VERIFIED** |
| **AC-4** | **UTF-8 BOM Prefix & RFC 4180 Escaping** | Streaming generator yields `codecs.BOM_UTF8` (`\ufeff`) followed by CSV rows formatted via `csv.writer` with `QUOTE_MINIMAL`. | `test_tc46_02_export_csv_download_and_content_verification`<br>`test_tc46_06_csv_escaping_commas_and_quotes` | 🟢 **VERIFIED** |
| **AC-5** | **Memory-Efficient Streaming for Large Candidate Volumes** | Uses generator yielding rows with `StreamingHttpResponse` and `Echo` buffer object, ensuring $O(1)$ memory consumption. | `test_tc46_02_export_csv_download_and_content_verification`<br>`test_tc46_07_empty_room_export_graceful_handling` | 🟢 **VERIFIED** |
| **AC-6** | **Strict RBAC & Tenant Isolation** | Protected by `IsRoomOwnerOrAdmin` permission class. Blocks students (403), unauthenticated users (401), and cross-organization recruiters (403). | `test_tc46_08_rbac_cross_tenant_isolation`<br>Unit: `ApplicantDataExportAPITests.test_rbac_*` | 🟢 **VERIFIED** |

---

## 4. Visual Evidence Archive

All visual verification screenshots were captured during test execution and saved in `CareerFlow/tests/reports/screenshots/`:

| Screenshot Filename | Verification Focus | Evidence Description |
| :--- | :--- | :--- |
| `us46_01_export_dropdown_mounted.png` | TC-46-01 | Rankings modal open with *"Export Data"* dropdown menu expanded showing CSV and Excel options. |
| `us46_02_export_csv_success.png` | TC-46-02 | CSV download initiated successfully; modal displays full candidate rankings leaderboard. |
| `us46_03_export_excel_success.png` | TC-46-03 | Excel (.xlsx) download triggered; status badge tags and score distributions verified. |
| `us46_04_shortlisted_filter_export.png` | TC-46-04 | *"Shortlisted Only"* toggle active; leaderboard isolated to candidate Alice; export parameters confirmed. |
| `us46_05_search_filter_export.png` | TC-46-05 | Search filter applied for *"Bob"*; candidate Bob Builder isolated and exported cleanly. |
| `us46_06_escaped_characters.png` | TC-46-06 | Leaderboard displaying Dr. Sarah "Sally" O'Connor, Ph.D. with quote and comma character handling. |
| `us46_07_empty_room_export.png` | TC-46-07 | Zero-state applicant room view displaying empty table with export buttons functioning cleanly. |
| `us46_08_rbac_forbidden.png` | TC-46-08 | Rogue recruiter session showing multi-tenant isolation with unauthorized rooms hidden. |

---

## 5. Notes & Observations

1. **Search Input Interaction:** In `RankedApplicantsModal.tsx`, the search query input (`input-ranked-search`) triggers candidate re-filtering when the user presses `Enter` (`onKeyDown={(e) => e.key === 'Enter' && fetchRankings(false)}`). The test suite simulates the `Enter` keystroke to accurately reflect user behavior.
2. **Backward Compatibility:** All existing endpoints (`/api/recruitment/rooms/{id}/rankings/` and downloadable report generators) continue to function with 100% test passing rate.
3. **OpenPyXL Integration:** The addition of `openpyxl>=3.1.2` in `backend/requirements.txt` operates cleanly without causing version conflicts or dependency bloat.

---

## 6. Peer QA Sign-Off

**Sign-Off Status:** 🟢 **APPROVED (VERIFIED & READY FOR MERGE)**  
**Peer QA Reviewer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin))  
**Lead Developer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222))  
**Target Branch:** `develop`  
**Date:** 2026-11-01  

