# Sprint 6 UI Testing Report — Task US-16-T6

**Sprint:** Sprint 6 (Epic 4: Video Presentation & AI)  
**User Story:** US-16: View Previous Presentation Analysis Results (Historical Practice Takes, Trajectory Telemetry & Standalone Analysis Reports)  
**Task:** US-16-T6 (Peer UI Testing, Tenant Isolation Verification & Automated Selenium Test Suite)  
**Author / Lead Developer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer)  
**Reviewer / UI Tester:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (from `feat/us-16-presentation-history`)  
**Date of Testing:** 2026-10-23  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** macOS 26.6.2 (Darwin arm64) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **9 / 9 Passed (100%)** (`tests/test_us16_presentation_history_ui.py`) in 51.65s | 🟢 **PASSED** |
| **Backend Unit & Security Tests** | **11 / 11 Passed (100%)** (`apps.presentation.tests.test_us16_presentation_history`) in 4.54s | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 1.18s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified & Enforced** | 🟢 **PASSED** |
| **Tenant Isolation & Security** | **100% Enforced** (`IsVideoOwner` guard, 403 Forbidden on foreign access, zero score/transcript leakage) | 🛡️ **SECURE** |
| **API Latency Performance** | **~185ms** (Well below the AC 6 maximum latency benchmark of 1.2s) | ⚡ **OPTIMAL** |
| **UI Test Suite Duration** | **51.65 seconds** | ⏱️ **OPTIMAL** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us16_presentation_history_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-16-01** | `test_tc16_01_empty_history_renders_welcoming_state_and_cta` | Student with 0 previous practice takes logs into `/login` and navigates to `/student/videos`; verifies welcoming zero-state card (`[data-testid='history-empty-state']`), descriptive onboarding copy, and "Start your first practice take" CTA button; clicks button and verifies immediate navigation to `/student/practice` (AC 5). | ✅ **PASSED** | ~6.2s |
| **TC-16-02** | `test_tc16_02_video_history_table_and_trajectory_metrics` | Student with 3 active takes visits `/student/videos`; asserts all 4 summary trajectory metrics cards: Total Reps (3), Average Composite Score (86/100), Top Score (92/100), and Average Speaking Pace (144 WPM); asserts table renders all 3 candidate rows with practice take titles, durations, recorded dates, color-coded score badges, and AI sub-signals chips (WPM, Eye Contact %, Posture %) (AC 1 & AC 2). | ✅ **PASSED** | ~6.5s |
| **TC-16-03** | `test_tc16_03_chronological_ordering_and_sorting` | Validates default chronological sorting: newest take appears at row #1 (`latest_take_2026_new.mp4`) and oldest take at row #3; tests interactive sorting dropdown (`[data-testid='select-history-sort']`): selects "Oldest First" (re-orders oldest to top) and "Highest Score" (re-orders 95/100 to top); verifies UI table updates deterministically (AC 3). | ✅ **PASSED** | ~6.4s |
| **TC-16-04** | `test_tc16_04_instant_search_and_status_filtering` | Tests client-side search input (`[data-testid='input-history-search']`): types "executive" to isolate `executive_ai_pitch.mp4`; clears search to restore all rows; tests status filter dropdown (`[data-testid='select-history-status']`): selects "Failed" to verify filtering down to `failed_take_sample.mp4` (AC 1 & AC 3). | ✅ **PASSED** | ~6.8s |
| **TC-16-05** | `test_tc16_05_in_page_analysis_modal_composite_score_and_breakdown` | Clicks Sparkles action button (`[data-testid='button-analysis-{id}']`); verifies in-page analysis modal mounts (`[data-testid='past-analysis-detail-modal']`); asserts composite score (89), speech breakdown (146 WPM), behavioral vision signals (Eye contact 91%, Posture 93%), AI coaching recommendations, and verbatim speech transcript; closes modal cleanly via X (AC 2). | ✅ **PASSED** | ~6.9s |
| **TC-16-06** | `test_tc16_06_video_preview_player_modal` | Clicks Play button (`[data-testid='button-play-take-{id}']`) on take row; asserts video playback modal mounts with `WebcamPlaybackPlayer`, duration display, and video specs banner (H.264 compressed size, duration); verifies "View AI Analysis" button transition. | ✅ **PASSED** | ~5.8s |
| **TC-16-07** | `test_tc16_07_dedicated_standalone_report_page` | Navigates directly to standalone report route `/presentation/history/:id`; asserts full-screen report header, composite score card (94), acoustic breakdown, behavioral signals, and AI suggestions list; verifies 1-click verbatim transcript copy button with clipboard feedback; clicks "← Back to Presentation History" and verifies return to `/student/videos` (AC 2). | ✅ **PASSED** | ~6.4s |
| **TC-16-08** | `test_tc16_08_strict_tenant_isolation_403_forbidden` | Student Alice uploads confidential take `alice_confidential_pitch.mp4`; Student Bob logs in and checks `/student/videos`: verifies Alice's video is completely hidden from Bob's history list; Bob navigates directly to Alice's report URL (`/presentation/history/{v_alice.id}`): verifies 403 Forbidden Access Denied warning renders, and Alice's score, title, and transcript are completely blocked from unauthorized viewing (AC 4). | ✅ **PASSED** | ~6.2s |
| **TC-16-09** | `test_tc16_09_high_performance_endpoint_latency` | Authenticates via JWT and measures wall-clock API response time for `GET /api/presentation/history/` across 5 comprehensive takes; verifies response time is ~185ms, easily satisfying the AC 6 threshold of <1.2 seconds (AC 6). | ✅ **PASSED** | ~0.4s |

---

### B. Backend Security & Unit Tests (`backend/apps/presentation/tests/test_us16_presentation_history.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_tc16_01_student_retrieves_empty_history_200_ok` | Verifies student with 0 previous takes receives HTTP 200 OK with empty list `[]`. | ✅ **PASSED** |
| `test_tc16_02_student_retrieves_presentation_history_chronological` | Verifies list of previous analyses is returned in descending order of `uploaded_at` (newest first). | ✅ **PASSED** |
| `test_tc16_03_tenant_isolation_student_only_views_own_videos` | Verifies strict tenant isolation: Student A cannot retrieve Student B's presentation videos via list endpoint. | ✅ **PASSED** |
| `test_tc16_04_tenant_isolation_detail_endpoint_forbidden_for_other_student` | Verifies `GET /api/presentation/history/<pk>/` returns HTTP 403 Forbidden if accessed by another student. | ✅ **PASSED** |
| `test_tc16_05_unauthenticated_access_rejected_401` | Verifies unauthenticated calls to history and detail endpoints return HTTP 401 Unauthorized. | ✅ **PASSED** |
| `test_tc16_06_video_detail_includes_all_analysis_submodels` | Verifies detail payload includes `speech_analysis`, `behavioral_analysis`, `presentation_score`, and `ai_feedback`. | ✅ **PASSED** |
| `test_tc16_07_status_filter_query_parameter` | Verifies query parameter `?status=COMPLETED` correctly filters results by processing status. | ✅ **PASSED** |
| `test_tc16_08_search_query_parameter` | Verifies query parameter `?search=pitch` filters results by matching `original_filename`. | ✅ **PASSED** |
| `test_tc16_09_student_can_delete_own_video` | Verifies student can delete their own past take, returning HTTP 204 No Content. | ✅ **PASSED** |
| `test_tc16_10_student_cannot_delete_other_students_video` | Verifies student attempting to delete another student's take receives HTTP 403 Forbidden. | ✅ **PASSED** |
| `test_tc16_11_performance_and_query_optimization` | Asserts list query uses `select_related` and `prefetch_related` to eliminate N+1 database queries. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verification

### ✅ AC 1: Student can view a list of their past presentation analyses
- **Verification:** Navigating to `/student/videos` fetches all previous takes for the authenticated student. The table displays take title, duration, recorded date, color-coded composite score pill, and key metric chips (WPM, Eye Contact %, Posture %).
- **Evidence:** Verified in automated UI tests `TC-16-02`, `TC-16-04` and backend unit test `test_tc16_02`.

### ✅ AC 2: Student can open any past analysis to view composite score, speech metrics, behavioral signals, and AI suggestions
- **Verification:** 
  1. **In-Page Drawer/Modal (`[data-testid='past-analysis-detail-modal']`):** Clicking the Sparkles icon on any row opens the full analysis modal. It renders the composite scorecard, speech breakdown (WPM, filler word count, clarity score), behavioral signals (eye contact %, posture %, engagement %), AI coaching recommendations, and verbatim transcript.
  2. **Dedicated Fullscreen Report (`/presentation/history/:id`):** Clicking "Full Report" opens the standalone page (`PresentationDetailReportPage`), complete with video player, scorecards, 1-click transcript copy button, and return navigation.
- **Evidence:** Verified in automated UI tests `TC-16-05`, `TC-16-07` and backend unit test `test_tc16_06`.

### ✅ AC 3: Results are listed chronologically, newest first (`-uploaded_at`)
- **Verification:** The backend endpoint `PresentationVideoHistoryView` explicitly orders by `-uploaded_at`. The frontend renders the newest take at row #1. The interactive sort dropdown supports dynamically switching to "Oldest First", "Highest Score", and "Longest Duration".
- **Evidence:** Verified in automated UI test `TC-16-03` and backend unit test `test_tc16_02`.

### ✅ AC 4: Strict tenant isolation: Students can only view their own presentation analyses (403 Forbidden on foreign access)
- **Verification:** The custom `IsVideoOwner` permission class strictly enforces object-level authorization on `/api/presentation/<pk>/` and `/api/presentation/history/<pk>/`. When a foreign student attempts to view or delete another student's take:
  1. The API returns HTTP `403 Forbidden`.
  2. The UI renders a dedicated security card: *"Tenant Isolation: Access Forbidden. You do not have permission to view another student’s presentation analysis."*
  3. No scores, transcripts, or video files are exposed.
- **Evidence:** Verified in automated UI test `TC-16-08` and backend unit tests `test_tc16_03`, `test_tc16_04`, and `test_tc16_10`.

### ✅ AC 5: Empty state displays a clear, welcoming graphic and call-to-action button linking to `/student/practice`
- **Verification:** When a student has no recorded takes, the table is replaced by the welcoming empty state card (`[data-testid='history-empty-state']`). It presents a video icon, encouraging guidance, and an action button ("Start your first practice take") that links directly to `/student/practice`.
- **Evidence:** Verified in automated UI test `TC-16-01` and backend unit test `test_tc16_01`.

### ✅ AC 6: High performance response time (<1.2s under standard network)
- **Verification:** `PresentationVideoHistoryView` employs `.select_related('speech_analysis', 'behavioral_analysis', 'presentation_score', 'ai_feedback')` and `.prefetch_related('execution_logs')` to eliminate N+1 queries. Live API latency tests measured a response time of **~185ms**, outperforming the 1.2-second requirement by over 80%.
- **Evidence:** Verified in automated benchmark test `TC-16-09` and backend unit test `test_tc16_11`.

---

## 4. UI Testing Evidence & Screenshots

All 8 screenshots were automatically captured during the live Selenium execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us16_01_empty_history_welcoming_state.png`](screenshots/us16_01_empty_history_welcoming_state.png) | Step 1: Empty History Welcoming Card | Displays clean video icon, encouraging explanation, and prominent "Start your first practice take" CTA button. |
| [`us16_02_video_history_table_and_trajectory_metrics.png`](screenshots/us16_02_video_history_table_and_trajectory_metrics.png) | Step 2: Trajectory Stats & Takes Table | Demonstrates 4 trajectory metric cards (Total Reps, Average Score, Top Score, Average Pace) and candidate table rows with score badges. |
| [`us16_03_chronological_ordering_and_sorting.png`](screenshots/us16_03_chronological_ordering_and_sorting.png) | Step 3: Chronological Sorting Controls | Shows newest take at top by default, and demonstrates interactive sort dropdown (Oldest First, Highest Score). |
| [`us16_04_instant_search_and_status_filtering.png`](screenshots/us16_04_instant_search_and_status_filtering.png) | Step 4: Search & Status Filters | Shows instant filename matching ("executive") and status dropdown filter ("Failed") isolating matching takes. |
| [`us16_05_in_page_analysis_modal_composite_score.png`](screenshots/us16_05_in_page_analysis_modal_composite_score.png) | Step 5: Past Analysis Detail Modal | Demonstrates modal mount with composite score (89/100), speech pacing (146 WPM), eye contact (91%), posture (93%), AI coaching tips, and verbatim transcript. |
| [`us16_06_video_preview_player_modal.png`](screenshots/us16_06_video_preview_player_modal.png) | Step 6: Video Preview Player Modal | Demonstrates in-modal video playback player, duration chips, compressed H.264 file specs banner, and analysis CTA. |
| [`us16_07_dedicated_standalone_report_page.png`](screenshots/us16_07_dedicated_standalone_report_page.png) | Step 7: Dedicated Fullscreen Report | Shows `/presentation/history/:id` standalone report view with video player, composite scorecard, behavioral signals, and 1-click transcript copy button. |
| [`us16_08_tenant_isolation_foreign_access_blocked.png`](screenshots/us16_08_tenant_isolation_foreign_access_blocked.png) | Step 8: Tenant Isolation 403 Guard | Shows strict security card: *"Tenant Isolation: Access Forbidden. You do not have permission to view another student’s presentation analysis."* |

---

## 5. Security & Multi-Tenant Isolation Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STUDENT PRESENTATION TENANT ISOLATION                    │
│                      Permission & Access Control Guard                      │
└─────────────────────────────────────────────────────────────────────────────┘
  Student Alice (ID: 101)                 Student Bob (ID: 102)
         │                                       │
         ▼                                       ▼
  GET /api/presentation/history/          GET /api/presentation/history/
  └── Filtered: user = Alice             └── Filtered: user = Bob
  └── Alice's takes (Visible)             └── Alice's takes (Hidden)
         │                                       │
         ▼                                       ▼
  GET /api/presentation/history/101/     GET /api/presentation/history/101/
  └── IsVideoOwner check: TRUE            └── IsVideoOwner check: FALSE
  └── HTTP 200 OK (Full Report)           └── HTTP 403 FORBIDDEN (Blocked)
```

1. **Object-Level Authorization (`IsVideoOwner`):**  
   Every presentation video and related sub-model endpoint validates ownership against `request.user`. Even if a malicious actor enumerates sequential video IDs, all foreign requests are rejected with HTTP 403 Forbidden.
2. **Zero Information Leakage:**  
   When unauthorized access is attempted, no sensitive metrics (composite scores, WPM, eye contact percentages) or private student transcripts are rendered.
3. **Optimized Database Aggregation:**  
   The history endpoint bundles child analyses with single-query efficiency, preventing database contention while maintaining isolation across student accounts.

---

## 6. Testing Observations & Resolutions

### Observation 1: User Re-creation Cascading Video Deletion in Test Setup
- **Symptom:** During initial test execution of TC-16-02, creating sample videos before calling `login_student` resulted in an empty history table.
- **Root Cause:** `create_user_in_db` in `conftest.py` executes `User.objects.filter(email__iexact=email).delete()` to ensure a fresh test user, which cascaded and deleted the sample videos created earlier in the test method.
- **Resolution:** Updated `login_student` helper in `tests/test_us16_presentation_history_ui.py` to check `if not User.objects.filter(email__iexact=email).exists():` before calling `create_user_in_db`.
- **Outcome:** Videos remain intact across the login workflow, executing with 100% determinism.

### Observation 2: Below-the-Fold Click Interception on Standalone Report
- **Symptom:** In TC-16-07, clicking the verbatim transcript copy button raised `ElementClickInterceptedException` due to vertical page height (y=1415px).
- **Resolution:** Added `driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", copy_btn)` prior to dispatching click events.
- **Outcome:** Clean execution with zero click interception across all viewport configurations.

---

## 7. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Unit & Security Tests:** 11/11 passed (`python backend/manage.py test apps.presentation.tests.test_us16_presentation_history`)
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors in 1.18s (`npm run build`)
- [x] **Automated Selenium UI Tests:** 9/9 test cases passed in 51.65s (`pytest tests/test_us16_presentation_history_ui.py`)
- [x] **Acceptance Criteria Verification:** AC 1 through AC 6 fully verified and documented
- [x] **Tenant Isolation Security:** Verified cross-student 403 Forbidden barriers on API and UI
- [x] **Performance Benchmark:** Confirmed <250ms endpoint latency, exceeding the <1.2s AC 6 requirement
- [x] **Visual Evidence Captured:** 8 high-resolution screenshots archived in `tests/reports/screenshots/`
- [x] **Git Repository Cleanliness:** No commits or pushes performed during testing, strictly maintaining review policy

---

## 8. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
> **Target Branch:** `develop`  
> **Summary Statement:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) has engineered a comprehensive, elegant, and secure implementation for US-16. The dual access pattern (interactive in-page modal + dedicated standalone report) provides exceptional UX flexibility. The trajectory metrics header allows students to quickly evaluate their presentation progress, and the tenant isolation security layer reliably protects student privacy. All 11 backend unit tests and 9 automated Selenium UI tests execute cleanly with a 100% pass rate. The feature is approved and ready for merge into `develop`.
