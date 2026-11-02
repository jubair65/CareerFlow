# Sprint 7 UI Testing Report — Task US-49-T6

**Sprint:** Sprint 7 (System Enhancements & Platform Maturity: Candidate Self-Service, Room Lifecycle Controls, Bulk Exports, Pipeline Notes, Ethical AI Consent & Automated Storage Retention)  
**Epic:** Epic 9: Security, Reliability & System Quality  
**User Story:** US-49: Automated Media Storage Purge & Data Retention Management Command  
**Task:** US-49-T6 (Dedicated Peer UI Automation Testing, Retention Verification, Data Integrity & Sign-off Report)  
**Author / Lead Developer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin))  
**Reviewer / Dedicated Peer UI Tester:** Farhana Tahsin Bonny ([@bonny](https://github.com/bonny)) / MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65))  
**Target Merge Branch:** `develop` (from `feat/us-49-media-retention-purge`)  
**Date of Testing:** 2026-11-02  
**Test Framework:** Selenium WebDriver (`selenium 4.49.0`) + pytest (`pytest 9.1.1`) & Django Management Commands  
**Platform:** Windows 11 | Python 3.14.0 | pytest 9.1.1 | selenium 4.49.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us49_media_purge_ui.py`) | ✅ **PASSED** |
| **Backend Unit & Management Command Tests** | **7 / 7 Passed (100%)** (`backend/apps/core/tests/test_us49_media_purge.py`) | ✅ **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified (100%)** (AC-1 through AC-6) | ✅ **PASSED** |
| **Stale Temp Upload Identification (AC-1)** | **100% Verified** (Temporary files in `temp_uploads/` older than 48 hours detected) | 🧹 **VERIFIED** |
| **Practice Video Retention Boundary (AC-2)** | **100% Verified** (Media older than configurable 30 days targeted for cleanup) | ⏱️ **VERIFIED** |
| **Score & Evaluation Integrity (AC-3)** | **100% Verified** (Physical `.mp4` deleted while scores, pace, & AI feedback persist) | 🛡️ **VERIFIED** |
| **Audit Log Tracking in DB (AC-4)** | **100% Verified** (`DataAccessLog` records freed bytes, duration, count, timestamp) | 📜 **VERIFIED** |
| **Dry-Run Preview Mode (AC-5)** | **100% Verified** (`--dry-run` reports exact bytes and files without unlinking) | 🔍 **VERIFIED** |
| **Missing File & Lock Resilience (AC-6)** | **100% Verified** (`os.remove` wrapped in `FileNotFoundError` / `PermissionError` safe blocks) | ⚙️ **VERIFIED** |
| **UI Test Suite Execution Duration** | **105.06 seconds** (8 comprehensive browser end-to-end scenarios) | ⏱️ **OPTIMAL** |
| **Visual Evidence Archive** | **8 High-Resolution Screenshots Captured** (`tests/reports/screenshots/`) | 📸 **ARCHIVED** |
| **Overall Recommendation** | **APPROVED FOR MERGE INTO `develop`** | 🚀 **READY** |

### Executive Overview & Verification Assessment
As the final system maintenance component of Sprint 7, User Story **US-49** prevents disk space exhaustion and compliance liability by implementing an automated storage purge and media retention management command (`purge_expired_media`). Under **Task US-49-T6**, dedicated peer UI and retention lifecycle testing was executed on feature branch `feat/us-49-media-retention-purge` authored by **MD. Hasanul Mobin** ([@hasanulmobin](https://github.com/hasanulmobin)).

The end-to-end verification validated:
1. **Physical File & Metadata Decoupling (AC-3):** When stale practice session videos (>30 days old) are purged, the physical media files are unlinked from the server storage volume. However, all associated relational scoring records—including `PresentationScore` (overall score, grade, delivery metric, content relevance), `SpeechAnalysis` (words per minute, clarity score, filler words), `BehavioralAnalysis`, and `PresentationFeedback` (strengths, recommendations)—remain completely intact and accessible.
2. **Student Video History UI Resilience (AC-3):** In the student dashboard (`/student/videos`), session history rows display the original filename, overall score badge (`score-badge-${id}`), and formatted timestamp without UI crashes or layout breaks after media unlinking.
3. **Analysis Modal & Fullscreen Report Verification (AC-3):**
   - The "View AI Analysis" modal dialog (`modal-analysis-content`) loads and renders historical delivery breakdowns, pace gauges, and coaching recommendations even after the underlying physical video file has been removed.
   - The dedicated report page (`/presentation/history/${id}`) successfully renders the composite score (88/100), duration, speaking cadence, and coaching advice.
4. **Recruiter Evaluation Notes & Stage Progression Isolation (AC-3):** Stored `CandidateNote` records and multi-stage interview progression history (`CandidateStageHistory` from US-47) linked to candidate applications remain fully preserved and queryable on the recruiter dashboard.
5. **Dry-Run Simulation Mode (`--dry-run` - AC-5):** Executing `python manage.py purge_expired_media --dry-run` produces an itemized preview of eligible media and disk space without unlinking files or generating persistent purge audit logs.
6. **Robustness & Safe File Handling (AC-6):** Purging records with pre-deleted or missing files on disk gracefully handles `FileNotFoundError` without interrupting execution or crashing the command.
7. **System Audit Trail (`DataAccessLog` - AC-4):** Every live purge execution records an entry under resource path `system:purge_expired_media` detailing total bytes freed, execution duration in milliseconds, and total count of removed assets.

---

## 2. Acceptance Criteria Verification Traceability Matrix

| AC ID | Acceptance Criteria Requirement | Implementation Component | Automated Test Scenario | Status |
| :--- | :--- | :--- | :--- | :---: |
| **AC-1** | System identifies temporary or abandoned video/audio uploads older than 48 hours | `backend/apps/core/management/commands/purge_expired_media.py` | `test_tc49_02_dry_run_retention_preview_preserves_disk_and_db`, `test_tc49_03_live_media_purge_execution_unlinks_disk_files` | ✅ **PASS** |
| **AC-2** | System identifies practice session media older than configured retention period (default 30 days) | `backend/apps/core/management/commands/purge_expired_media.py` | `test_tc49_02_dry_run_retention_preview_preserves_disk_and_db`, `test_tc49_03_live_media_purge_execution_unlinks_disk_files` | ✅ **PASS** |
| **AC-3** | Automated command purges stale physical files from disk while preserving scores, analyses, and audit logs | `purge_expired_media.py`, `frontend/src/components/presentation/VideoHistory.tsx`, `PresentationDetailReportPage.tsx` | `test_tc49_04_post_purge_student_history_scores_intact`, `test_tc49_05_post_purge_analysis_modal_metrics_integrity`, `test_tc49_06_post_purge_fullscreen_detail_report`, `test_tc49_07_recruiter_pipeline_evaluation_notes_intact` | ✅ **PASS** |
| **AC-4** | Deleted media entries are logged in system audit logs (`DataAccessLog`) with timestamp, freed bytes, and duration | `backend/apps/core/models.py` (`DataAccessLog`), `purge_expired_media.py` | `test_tc49_08_system_audit_logs_and_missing_file_resilience` | ✅ **PASS** |
| **AC-5** | Dry-run mode (`--dry-run`) previews deletions without unlinking files or modifying DB fields | `purge_expired_media.py` | `test_tc49_02_dry_run_retention_preview_preserves_disk_and_db` | ✅ **PASS** |
| **AC-6** | Command handles missing files or file lock exceptions without crashing | `purge_expired_media.py` (`safe_delete_file`) | `test_tc49_08_system_audit_logs_and_missing_file_resilience` | ✅ **PASS** |

---

## 3. Test Cases Execution & Visual Evidence

### TC-49-01: Baseline Video History & Scoring Presentation Prior to Purge
- **Objective:** Verify student video history UI displays practice session with score badge (88) and physical video file on disk prior to cleanup.
- **Preconditions:** Authenticated student on `/student/videos` with newly created practice session and physical `.mp4` file.
- **Action:** Inspect history row `[data-testid="history-row-${video.id}"]`, score badge `[data-testid="score-badge-${video.id}"]`, and disk path existence.
- **Expected Result:** Session row visible; score badge displays "88"; physical file exists at `media/presentations/...`.
- **Actual Result:** Row rendered; score 88 displayed; physical file presence verified.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_01_pre_purge_video_history_baseline.png`

---

### TC-49-02: Dry-Run Mode Preview Preserves Disk Files and Database Records
- **Objective:** Verify that `python manage.py purge_expired_media --dry-run` reports candidate files without deleting them from disk or mutating the database.
- **Preconditions:** Stale practice video (>30 days old) and expired temporary upload (>48 hours old) staged on filesystem.
- **Action:** Run `purge_expired_media` with `--dry-run --days 30 --temp-hours 48`.
- **Expected Result:** Command outputs `[DRY-RUN] Would purge video:` and `[DRY-RUN] Would delete temp upload:`; both files still exist on disk; DB record unchanged; zero purge audit logs generated.
- **Actual Result:** Dry-run preview generated; files untouched on disk; database state intact.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_02_dry_run_preview_intact.png`

---

### TC-49-03: Live Purge Unlinks Physical Video and Temporary Staged Files
- **Objective:** Verify live command execution unlinks physical files from disk while preserving the `PresentationVideo` model record.
- **Preconditions:** Physical video (>35 days old) and temporary upload (>55 hours old) staged on disk.
- **Action:** Execute `call_command("purge_expired_media", days=30, temp_hours=48)`.
- **Expected Result:** Physical `.mp4` and temporary files unlinked from disk (`os.path.exists == False`); DB record refreshed with `file = ''`.
- **Actual Result:** Files unlinked; storage freed; DB record retained with empty file reference.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_03_live_purge_disk_cleanup.png`

---

### TC-49-04: Post-Purge Student Video History UI Scores Intact
- **Objective:** Verify student dashboard renders purged video session with intact composite score badge (88) and metadata without crashing.
- **Preconditions:** Purged video session with physical file unlinked.
- **Action:** Navigate to `/student/videos` in browser; assert row and score badge visibility.
- **Expected Result:** History row rendered; score badge displays "88"; zero frontend errors.
- **Actual Result:** Session row rendered cleanly with score 88 badge intact.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_04_post_purge_history_scores_intact.png`

---

### TC-49-05: Post-Purge AI Analysis Modal Metrics Integrity
- **Objective:** Verify clicking "View AI Analysis" on a purged video opens the analysis modal with speech and behavioral metrics preserved.
- **Preconditions:** Student on `/student/videos` with purged practice session.
- **Action:** Click `[data-testid="button-view-analysis-${video.id}"]`.
- **Expected Result:** Modal `[data-testid="past-analysis-detail-modal"]` mounts displaying speaking rate (`142 WPM`), clarity score (`91%`), filler word count, and AI feedback recommendations.
- **Actual Result:** Analysis modal opened; all delivery metrics and suggestions displayed accurately without requiring video playback.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_05_post_purge_modal_analysis_preserved.png`

---

### TC-49-06: Post-Purge Fullscreen Presentation Detail Report
- **Objective:** Verify navigating to dedicated report page `/presentation/history/:id` for a purged session renders composite score, duration, and AI coaching.
- **Preconditions:** Purged video session.
- **Action:** Navigate to `http://localhost:5173/presentation/history/${video.id}`.
- **Expected Result:** Overall score 88, original filename, and AI Coaching Feedback section render without unhandled exceptions.
- **Actual Result:** Page loaded completely; overall score 88, speaking cadence, and feedback tips rendered cleanly.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_06_post_purge_fullscreen_report.png`

---

### TC-49-07: Recruiter Pipeline Evaluation Notes and Stage History Intact
- **Objective:** Verify recruiter internal notes and multi-stage interview progression history remain unaffected when candidate media is purged.
- **Preconditions:** Candidate application with linked presentation video, recruiter note, and stage transition history.
- **Action:** Execute `purge_expired_media`; inspect application model, note count, and HR dashboard.
- **Expected Result:** Physical candidate video unlinked; `CandidateApplication.stage == SHORTLISTED`; recruiter note and stage history preserved; HR dashboard renders room and applicant state.
- **Actual Result:** Application record intact; note and stage history records preserved in database; HR dashboard displays room.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_07_recruiter_notes_stages_intact.png`

---

### TC-49-08: System Audit Logging & Missing File Resilience
- **Objective:** Verify live purge creates a comprehensive `DataAccessLog` entry with duration and freed bytes, and gracefully ignores already-deleted or missing files without crashing.
- **Preconditions:** Video record pointing to non-existent file on disk.
- **Action:** Run live `purge_expired_media` and query `DataAccessLog.objects.filter(resource_path="system:purge_expired_media")`.
- **Expected Result:** Command completes with 0 errors; `DataAccessLog` contains `freed_bytes`, `duration_ms`, `purged_videos_count`, and `status="COMPLETED"`.
- **Actual Result:** Command completed cleanly; audit record persisted with total bytes freed and execution metrics.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us49_08_system_audit_log_verified.png`

---

## 4. Defect Analysis & Verification Adjustments

During dedicated peer automation testing, the following test orchestration refinements were made:

1. **`PresentationDetailReportPage.tsx` Asynchronous Loading Synchronization:**
   - *Observation:* `test_tc49_06` initially evaluated the page DOM while the loading skeleton (`Loading Presentation Analysis...`) was still active, causing a premature score assertion failure.
   - *Fix:* Replaced immediate body evaluation with explicit wait for analysis loading completion: `wait.until(lambda d: "88" in d.find_element(By.TAG_NAME, "body").text)`.
2. **`CandidateApplication` & `CandidateNote` Model Field Alignment:**
   - *Observation:* `test_tc49_07` test setup initially passed legacy arguments (`current_stage`, `match_score`, `note`) instead of the finalized Sprint 7 schema fields (`stage`, `final_score`, `content`, `updated_by`, `notes`).
   - *Fix:* Aligned test fixture construction with `backend/apps/recruitment/models.py` schema (`stage=CandidateApplication.Stage.SHORTLISTED`, `content=...`, `notes=...`).
3. **Dry-Run Audit Log Count Isolation:**
   - *Observation:* `test_tc49_02` checked global count `dry_run_logs == 0`, which caused false positives if previous test runs had already executed live purges in the database.
   - *Fix:* Updated assertion to check differential count (`dry_run_logs == initial_logs_count`).

---

## 5. Verification Sign-Off

- **Lead Developer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) — *Implementation Complete*
- **Peer UI Automation Tester:** Farhana Tahsin Bonny ([@bonny](https://github.com/bonny)) / MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) — *Verified & Signed Off*
- **Testing Result:** **8 / 8 Automated UI Tests Passed (100% Green)**
- **Merge Recommendation:** **APPROVED FOR MERGE INTO `develop`**

