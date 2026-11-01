# Sprint 7 UI Testing Report — Task US-48-T6

**Sprint:** Sprint 7 (System Enhancements & Platform Maturity: Candidate Self-Service, Room Lifecycle Controls, Bulk Exports, Pipeline Notes, Ethical AI Consent & Automated Storage Retention)  
**Epic:** Epic 9: Security, Compliance & Platform Reliability  
**User Story:** US-48: AI Biometric & Evaluation Consent Notice Gatekeeper  
**Task:** US-48-T6 (Dedicated Peer UI Automation Testing, Consent Modal Gatekeeper, Audit Trail Verification & Sign-off Report)  
**Author / Lead Developer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin))  
**Reviewer / Dedicated Peer UI Tester:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65))  
**Target Merge Branch:** `develop` (from `feat/us-48-ai-biometric-consent`)  
**Date of Testing:** 2026-11-02  
**Test Framework:** Selenium WebDriver (`selenium 4.49.0`) + pytest (`pytest 9.1.1`) & Django TestCase  
**Platform:** Windows 11 | Python 3.14.0 | pytest 9.1.1 | selenium 4.49.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Microsoft Edge Headless  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **8 / 8 Passed (100%)** (`tests/test_us48_ai_consent_ui.py`) | ✅ **PASSED** |
| **Backend Unit & Integration Tests** | **12 / 12 Passed (100%)** (`backend/apps/core/tests/test_us48_ai_consent.py`) | ✅ **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified (100%)** (AC-1 through AC-6) | ✅ **PASSED** |
| **Consent Gatekeeper Interception** | **100% Verified** (Webcam recording, file upload & applicant portal blocked before consent) | 🔒 **VERIFIED** |
| **Accessible Biometric Notice Modal** | **100% Verified** (`AIConsentModal.tsx` audio, facial telemetry, retention disclosures) | 📋 **VERIFIED** |
| **Consent Decision Engine (Agree / Decline)** | **100% Verified** (Agree unlocks ingestion; Decline displays banner without errors) | 🛡️ **VERIFIED** |
| **Audit Logging & Cryptographic Tokens** | **100% Verified** (`AIConsentLog` records IP, user agent, token, timestamp, policy v1.0) | 📜 **VERIFIED** |
| **Backend 403 Forbidden Gatekeeper** | **100% Verified** (`verify_ai_consent` blocks direct API upload without consent) | 🛑 **ENFORCED** |
| **UI Test Suite Execution Duration** | **151.80 seconds** (8 comprehensive browser end-to-end scenarios) | ⏱️ **OPTIMAL** |
| **Visual Evidence Archive** | **8 High-Resolution Screenshots Captured** (`tests/reports/screenshots/`) | 📸 **ARCHIVED** |
| **Overall Recommendation** | **APPROVED FOR MERGE INTO `develop`** | 🚀 **READY** |

### Executive Overview & Verification Assessment
As part of Sprint 7 compliance and platform reliability, User Story **US-48** introduces a mandatory consent notice gatekeeper to ensure candidate awareness and explicit consent before AI biometric feature extraction, facial posture tracking, or automated speech telemetry are performed. Under **Task US-48-T6**, dedicated peer UI automation testing was conducted by **MD. Jubair Bin Hasan** ([@jubair65](https://github.com/jubair65)) on feature branch `feat/us-48-ai-biometric-consent` authored by **MD. Hasanul Mobin** ([@hasanulmobin](https://github.com/hasanulmobin)).

The verification validated:
1. **Consent Notice Dialog Gatekeeper (`AIConsentModal.tsx` - AC-1, AC-2, AC-3):** Attempting to start a webcam presentation recording or selecting a video file without prior consent instantly intercepts the user with `modal-ai-consent`. The modal clearly presents disclosures covering audio telemetry, facial orientation/posture tracking, human-in-the-loop recruiter oversight, and automated data retention policies adhering to GDPR Article 9 & EU AI Act requirements.
2. **Agree & Unlock Workflow (AC-3):** Checking `checkbox-ai-consent-agree` enables `button-ai-consent-agree`. Clicking the button records consent on the backend, issues a secure consent token, closes the modal, and unlocks camera recording or proceeds with video file processing.
3. **Decline & Clean Cancellation Workflow (AC-3):** Clicking `button-ai-consent-decline` cleanly dismisses the modal without recording or uploading any video data. It renders `alert-ai-consent-refused` explaining that AI consent is required, accompanied by `button-reopen-ai-consent` allowing users to reconsider at any time.
4. **Public Applicant Portal Ingestion Gate (AC-4):** In `/apply/:token` (`PublicApplicationPage.tsx`), candidate video file dropzone selection triggers the consent modal before submitting application video data.
5. **Immutable Audit Logging (`AIConsentLog` - AC-5):** Every consent decision is recorded in MySQL with policy version (`v1.0`), client IP address, user agent, cryptographically random `consent_token`, user/email identifier, and precise UTC timestamp.
6. **Backend Gatekeeper Enforcement (US-48-T5):** Direct API requests to `POST /api/presentation/upload/` without consent authorization are strictly rejected with `HTTP 403 Forbidden` and error code `AI_CONSENT_REQUIRED`.

---

## 2. Acceptance Criteria Verification Traceability Matrix

| AC ID | Acceptance Criteria Requirement | Implementation Component | Automated Test Scenario | Status |
| :--- | :--- | :--- | :--- | :---: |
| **AC-1** | Mandatory AI Biometric & Evaluation disclosure presented before recording or uploading video presentation | `frontend/src/components/presentation/AIConsentModal.tsx`, `VideoRecorder.tsx` | `test_tc48_01_consent_modal_blocking_on_webcam_start` | ✅ **PASS** |
| **AC-2** | Structured notice covers audio telemetry, facial orientation, human oversight, and data retention policies | `backend/apps/core/views.py` (`AIConsentPolicyView`), `AIConsentModal.tsx` | `test_tc48_05_dedicated_policy_link_accessibility` | ✅ **PASS** |
| **AC-3** | Explicit Agree checkbox enables confirmation button; Decline cleanly dismisses without recording | `AIConsentModal.tsx`, `VideoRecorder.tsx` | `test_tc48_02_agree_and_unlock_webcam_recording`, `test_tc48_03_decline_and_cancel_cleanly_aborts` | ✅ **PASS** |
| **AC-4** | Public candidate applicant portal enforces consent gate prior to video presentation submission | `frontend/src/pages/PublicApplicationPage.tsx`, `AIConsentModal.tsx` | `test_tc48_06_applicant_portal_video_upload_gate` | ✅ **PASS** |
| **AC-5** | Immutable consent audit log persists user/email, IP address, user agent, policy version, and token | `backend/apps/core/models.py` (`AIConsentLog`), `backend/apps/core/views.py` | `test_tc48_07_audit_record_persistence` | ✅ **PASS** |
| **AC-6** | Permanent, unauthenticated link to view current AI Biometric & Evaluation Policy terms | `frontend/src/components/presentation/AIConsentModal.tsx`, `VideoRecorder.tsx` | `test_tc48_05_dedicated_policy_link_accessibility` | ✅ **PASS** |

---

## 3. Test Cases Execution & Visual Evidence

### TC-48-01: Consent Modal Blocking on Webcam Start
- **Objective:** Verify that clicking "Start Recording" without prior consent halts camera activation and mounts the accessible consent modal.
- **Preconditions:** Authenticated student on `/student/presentation` with zero prior consent records in database or localStorage.
- **Action:** Click `[data-testid="button-start-recording"]`.
- **Expected Result:** `[data-testid="modal-ai-consent"]` mounts with header "AI Biometric & Evaluation Consent Notice". Camera recording is blocked.
- **Actual Result:** Modal displayed immediately; recording prevented.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_01_consent_modal_blocking.png`

---

### TC-48-02: Agree & Unlock Webcam Recording
- **Objective:** Verify that checking agreement and clicking "I Agree & Continue" records consent and unlocks recording.
- **Preconditions:** `[data-testid="modal-ai-consent"]` is open.
- **Action:** Check `[data-testid="checkbox-ai-consent-agree"]` and click `[data-testid="button-ai-consent-agree"]`.
- **Expected Result:** Modal cleanly closes; consent token is stored in localStorage; camera recording UI is unlocked.
- **Actual Result:** Modal dismissed, `careerflow_ai_consent_token` set, recording controls active.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_02_consent_agreed_recording_unlocked.png`

---

### TC-48-03: Decline & Cancel Cleanly Aborts
- **Objective:** Verify that declining consent dismisses the modal without recording and presents an informative alert banner.
- **Preconditions:** Unconsented student session on `/student/presentation`.
- **Action:** Trigger consent modal and click `[data-testid="button-ai-consent-decline"]`.
- **Expected Result:** Modal closes; zero video data is ingested; `[data-testid="alert-ai-consent-refused"]` displays guidance with `[data-testid="button-reopen-ai-consent"]`.
- **Actual Result:** Consent declined cleanly, explanation banner rendered with reconsider button.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_03_consent_declined_alert_shown.png`

---

### TC-48-04: File Upload Consent Gate
- **Objective:** Verify that unconsented users selecting or uploading video files are intercepted by the consent modal.
- **Preconditions:** Unconsented student on `/student/presentation` in "Upload Video File" tab.
- **Action:** Click upload submit button or trigger file selection input.
- **Expected Result:** `[data-testid="modal-ai-consent"]` appears, blocking file processing until consent is provided.
- **Actual Result:** File ingestion intercepted by modal dialog.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_04_file_upload_consent_modal.png`

---

### TC-48-05: Dedicated Policy Link Accessibility (AC-2, AC-6)
- **Objective:** Verify that clicking the AI policy privacy notice link opens the policy in an inspectable, read-only mode without requiring agree/decline buttons.
- **Preconditions:** Student navigated to `/student/presentation`.
- **Action:** Click `[data-testid="link-ai-consent-policy"]`.
- **Expected Result:** `[data-testid="modal-ai-consent"]` opens in read-only mode showing all policy sections (audio telemetry, facial tracking, data retention); footer displays "Close Notice" button without agreement checkbox.
- **Actual Result:** Policy opened in read-only mode with sections and "Close Notice" button.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_05_policy_notice_modal_inspectable.png`

---

### TC-48-06: Applicant Portal Video Upload Gate (AC-4)
- **Objective:** Verify that external job candidates applying via public link (`/apply/:token`) are gated by the consent notice before submitting video presentations.
- **Preconditions:** Open recruitment room with valid share token; candidate inputs name and email.
- **Action:** Select video file via `[data-testid="input-video-file"]`.
- **Expected Result:** Consent modal mounts, preventing video attachment until consent is granted.
- **Actual Result:** Modal cleanly intercepted file dropzone and required consent agreement.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_06_applicant_portal_consent_modal.png`

---

### TC-48-07: Audit Record Persistence (AC-5)
- **Objective:** Verify that agreeing to consent creates an immutable database record in `AIConsentLog` with IP address, user agent, policy version, and token.
- **Preconditions:** Consent agreement submitted via frontend dialog.
- **Action:** Query `AIConsentLog.objects.filter(user=student)` in database.
- **Expected Result:** Record exists with `agreed=True`, `policy_version="v1.0"`, non-empty `consent_token`, valid `ip_address`, and `user_agent`.
- **Actual Result:** DB record confirmed with all required audit fields populated.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_07_audit_log_persisted_in_db.png`

---

### TC-48-08: Backend Gatekeeper 403 Enforcement (US-48-T5)
- **Objective:** Verify that direct API upload requests to `POST /api/presentation/upload/` without a valid consent token are strictly rejected with HTTP 403.
- **Preconditions:** Authenticated student without consent record.
- **Action:** Send raw multipart HTTP POST to `/api/presentation/upload/` with file payload.
- **Expected Result:** Response status `403 Forbidden` with JSON code `AI_CONSENT_REQUIRED`.
- **Actual Result:** HTTP 403 Forbidden received; subsequent upload with `X-AI-Consent-Token` header permitted.
- **Status:** ✅ **PASS**
- **Visual Evidence:** `tests/reports/screenshots/us48_08_backend_gatekeeper_403_enforced.png`

---

## 4. Peer Review Defect Fixes & Code Quality Adjustments

During dedicated peer UI testing, the following defect was identified and rectified:

1. **`PublicApplicationPage.tsx` Missing Component Mount & Import:**
   - *Defect:* Although consent state (`hasConsented`, `isConsentModalOpen`, handlers) was declared, the component `<AIConsentModal>` was never rendered in the JSX return tree, and `getStoredAIConsentToken` was missing from imports, causing runtime errors when candidates dropped video files.
   - *Resolution:* Added import of `getStoredAIConsentToken` and `AIConsentModal`, and mounted `<AIConsentModal>` in the page layout.
2. **`VideoRecorder.tsx` Start Recording Button Accessibility:**
   - *Defect:* The "Start Recording" button had `disabled={!isCameraActive || isProcessing}` which prevented users in headless or camera-inactive sessions from clicking the button to trigger the consent modal.
   - *Resolution:* Updated to `disabled={(hasConsented && !isCameraActive) || isProcessing}` so unconsented users can click "Start Recording" to mount the modal.
3. **`verify_ai_consent` Localhost IP Fallback Contamination:**
   - *Defect:* `verify_ai_consent` previously contained a fallback check matching `AIConsentLog` by IP address alone (`ip_address=client_ip`). In local testing environments (`127.0.0.1`), one agreed test caused all subsequent unconsented test users to be treated as consented.
   - *Resolution:* Removed the IP address fallback so consent strictly requires a verified token header, candidate email, or authenticated user record.
4. **Agency Rooms Page Responsive Action Buttons Layout (`AgencyRoomsPage.tsx`):**
   - *Defect:* In `AgencyRoomsPage.tsx`, the action buttons (`Criteria`, `Weights`, `Shortlist`) and the room status select dropdown (`select-room-status`) overflowed the card boundary on medium screens, cutting off the status text into `[Activ`.
   - *Resolution:* Removed `min-w-0` and `shrink-0` constraints, allowing buttons and status select to wrap naturally without clipping.

---

## 5. Verification Sign-Off

- **Lead Developer:** MD. Hasanul Mobin ([@hasanulmobin](https://github.com/hasanulmobin)) — *Implementation Complete*
- **Peer UI Automation Tester:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) — *Verified & Signed Off*
- **Testing Result:** **8 / 8 Automated UI Tests Passed (100% Green)**
- **Merge Recommendation:** **APPROVED FOR MERGE INTO `develop`**

