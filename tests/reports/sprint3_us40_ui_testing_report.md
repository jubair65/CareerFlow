# Sprint 3 UI Testing Report — Task US-40-T6

**Sprint:** Sprint 3 (Presentation AI)  
**User Story:** US-40: AI Pipeline Failure Handling & Pipeline Resilience  
**Task:** US-40-T6 (UI Testing for Failure Notification, Diagnostics & Recovery UI)  
**Tester / Developer:** Nafisa Tabassum Maria (System Architect)  
**Date:** 2026-09-30  
**Framework:** Selenium WebDriver + pytest  
**Platform:** macOS (Apple Silicon arm64) | Python 3.14.2 | pytest 9.1.1  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Total Test Cases** | **5** |
| **Passed** | **5 (100%)** |
| **Failed** | **0 (0%)** |
| **Execution Duration** | **21.98 seconds** |
| **Overall Status** | 🟢 **PASSED & VERIFIED** |

---

## 2. Test Execution Matrix

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-US40-T6-01** | `test_tc_us40_t6_01_failed_pipeline_renders_alert_and_retry_cta` | Candidate views Presentation Studio with a failed video take; verifies `PipelineStatusAlert` mounts with high-contrast failure alert, "Fault Caught (US-40)" badge, status badge in red, and accessible **[Retry Analysis]** CTA button. | ✅ **PASSED** | ~4.4s |
| **TC-US40-T6-02** | `test_tc_us40_t6_02_diagnostics_drawer_toggle_and_log_rendering` | Candidate clicks **[Diagnostics]** toggle; verifies collapsible telemetry drawer expands to reveal structured chronological execution logs (`SPEECH_ANALYSIS`, `VISION_ANALYSIS`), attempts, and error details without page reload. | ✅ **PASSED** | ~4.2s |
| **TC-US40-T6-03** | `test_tc_us40_t6_03_graceful_degradation_alert_and_100_percent_speech_mode` | Video frames lack valid computer vision facial landmarks; verifies graceful degradation banner mounts with "100% Speech Mode" tag, friendly explanation, and **[Re-run Analysis]** action button. | ✅ **PASSED** | ~4.3s |
| **TC-US40-T6-04** | `test_tc_us40_t6_04_retrying_state_badge_and_animation` | Pipeline is undergoing transient retry with exponential backoff; verifies animated recovery banner displays with pulsing loader and "Attempting Recovery" badge. | ✅ **PASSED** | ~4.5s |
| **TC-US40-T6-05** | `test_tc_us40_t6_05_retry_button_click_triggers_recovery` | Candidate clicks **[Retry Analysis]** button; verifies interactive state transition, asynchronous API trigger to `/api/presentation/<video_id>/retry/`, and responsive UI feedback. | ✅ **PASSED** | ~4.6s |

---

## 3. Acceptance Criteria Verified

- ✅ **Automatic Fault Interception & Banner Display:** When any stage of the video presentation pipeline encounters an unrecoverable exception, `PipelineStatusAlert` intercepts the error state and renders a clean, user-friendly recovery card rather than crashing the page or showing unformatted 500 error popups.
- ✅ **One-Click Supervised Retry Action:** Candidates can trigger an automatic recovery re-run directly via `[data-testid='button-pipeline-retry']`. The request re-invokes the pipeline manager with exponential backoff and jitter.
- ✅ **Execution Log Telemetry Drawer:** An expandable diagnostics panel displays each processing stage, attempt counts, execution duration in milliseconds, and human-readable diagnostic messages.
- ✅ **Graceful Degradation for Real-World Quality:** When low lighting, camera tilt, or video corruption prevents MediaPipe facial tracking from extracting landmarks, the system does not fail the video. It gracefully switches to 100% speech scoring, sets `has_behavioral_data=False`, marks the video as `PARTIALLY_COMPLETED`, and explains this clearly on the UI.
- ✅ **Live Retrying State Animation:** During transient retries with exponential backoff, the UI presents an animated status notification reassuring the candidate that recovery is in progress.
- ✅ **Video History Integration:** The same resilient recovery and diagnostics controls are available within the individual video analysis drawer in `VideoHistory.tsx`.

---

## 4. Test Environment & Artifacts

- **UI Automation Test Suite:** [`tests/test_us40_pipeline_resilience_ui.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/test_us40_pipeline_resilience_ui.py)
- **Backend Unit Test Suite:** [`backend/apps/presentation/tests/test_pipeline_resilience.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/presentation/tests/test_pipeline_resilience.py) (6/6 unit tests passed)
- **Pipeline Manager Service:** [`backend/apps/presentation/services/pipeline_manager.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/presentation/services/pipeline_manager.py)
- **Database Model & Migrations:** [`backend/apps/presentation/models.py`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/backend/apps/presentation/models.py) (`PipelineExecutionLog`, Migration `0006_alter_presentationvideo_status_pipelineexecutionlog.py`)
- **Frontend Alert Component:** [`frontend/src/components/presentation/PipelineStatusAlert.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/components/presentation/PipelineStatusAlert.tsx)
- **Integration Pages:** [`frontend/src/pages/PresentationStudio.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/pages/PresentationStudio.tsx), [`frontend/src/pages/VideoHistory.tsx`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/frontend/src/pages/VideoHistory.tsx)
- **Architecture Documentation:** [`docs/us40_pipeline_resilience_architecture.md`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/docs/us40_pipeline_resilience_architecture.md)
- **Report Location:** [`tests/reports/sprint3_us40_ui_testing_report.md`](file:///Users/nafisatabassummaria/Study/3.2/Project/CareerFlow/tests/reports/sprint3_us40_ui_testing_report.md)
