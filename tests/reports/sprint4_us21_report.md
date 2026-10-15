# Sprint 4 UI & Unit Testing Report — Task US-21-T6

**Sprint:** Sprint 4 (Recruitment Rooms & Candidate Submission)  
**User Story:** US-21: Shareable Application Link  
**Task:** US-21-T6 (Peer Testing & Code Review for Shareable Application Link & Candidate Portal)  
**Peer Tester / Reviewer:** Tahsin Bonny (@tahsinbonnie98) (Software Developer & Peer Tester)  
**Developer:** Jannatun Naeem Mona (@jn-mona04) (System Analyst / BA)  
**Date:** 2026-10-07  
**Framework:** Selenium WebDriver + pytest & Django REST Framework APITestCase  
**Platform:** Windows 11 | Python 3.14.3 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`)  
**Browser:** Google Chrome (Headless)  

---

## 1. Executive Summary

| Metric | Result |
| :--- | :--- |
| **Backend Unit Tests** | **14 / 14 Passed (100%)** (`backend/apps/recruitment/tests/test_shareable_link.py`) |
| **Total Automated UI Test Cases** | **6** (`tests/test_us21_shareable_link_ui.py`) |
| **UI Suite Status** | **6 / 6 Passed (100%)** |
| **Defects Caught & Resolved** | **3** (Token entropy, stale `updated_at`, closed room error code) |
| **Backend Test Duration** | **128.07 seconds** |
| **Automated Suite Status** | 🟢 **PASSED & VERIFIED** |
| **Overall Recommendation** | 🟢 **APPROVED FOR MERGE INTO `develop`** |

---

## 2. Test Execution Matrix

### A. Backend Unit Tests (`apps/recruitment/tests/test_shareable_link.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_token_generation_format_and_security` | Verifies tokens are URL-safe, non-guessable, and contain at least 32 bytes of cryptographic entropy. | ✅ **PASSED** |
| `test_room_auto_generates_share_token` | Asserts newly created room automatically receives an active `share_token` and `link_is_active=True`. | ✅ **PASSED** |
| `test_get_link_as_owner_success` | Verifies HR owner can retrieve shareable link details, full URL, expiration state, and active status. | ✅ **PASSED** |
| `test_post_link_as_owner_returns_or_creates_token` | Verifies POST to `/link/` retrieves existing token or provisions initial token idempotently. | ✅ **PASSED** |
| `test_public_resolution_unauthenticated_success` | Validates candidates can access public job opening via token without login, retrieving title, company, skills, and weights. | ✅ **PASSED** |
| `test_public_resolution_invalid_token_returns_404` | Non-existent or forged token returns HTTP 404 Not Found with `LINK_NOT_FOUND` code. | ✅ **PASSED** |
| `test_deactivate_link_as_owner` | HR owner can deactivate link via `/link/deactivate/`; asserts immediate HTTP 410 Gone with `LINK_DEACTIVATED` for candidates. | ✅ **PASSED** |
| `test_activate_link_restores_public_access` | HR owner can reactivate link via `/link/activate/`; asserts restoration of HTTP 200 OK for applicants. | ✅ **PASSED** |
| `test_regenerate_link_generates_new_token_and_invalidates_old` | Regenerating issues fresh 32-byte token; old token returns HTTP 404 while new token resolves successfully. | ✅ **PASSED** |
| `test_expired_link_returns_410_gone` | Rooms with past `link_expires_at` return HTTP 410 Gone with `LINK_EXPIRED` code. | ✅ **PASSED** |
| `test_closed_room_returns_410_gone` | Rooms with status `CLOSED` reject public candidate access with HTTP 410 Gone. | ✅ **PASSED** |
| `test_unauthenticated_cannot_manage_link` | Unauthenticated requests to link management endpoints return HTTP 401 Unauthorized. | ✅ **PASSED** |
| `test_student_cannot_manage_link` | Student/Applicant role cannot access or modify room link endpoints (HTTP 403 Forbidden). | ✅ **PASSED** |
| `test_other_hr_cannot_manage_or_view_link` | Lateral tenant isolation: another HR manager cannot view or mutate another owner's room link (HTTP 404). | ✅ **PASSED** |

### B. Automated UI Tests (`tests/test_us21_shareable_link_ui.py`)

| Test Case ID | Test Method Name | Description | Status |
| :--- | :--- | :--- | :---: |
| **TC-US21-01** | `test_tc_us21_01_modal_mount_from_room_card` | HR navigates to `/hr/rooms`; clicks link action button on room card; verifies modal mounts with hiring room title, company name, US-21 tag, and active status badge; verifies clean dismissal via close button. | ✅ **PASSED** |
| **TC-US21-02** | `test_tc_us21_02_copy_link_clipboard_and_feedback` | HR inspects read-only application URL input (`/apply/<token>`); clicks "Copy Link"; verifies button reactively transitions to "Copied!" with green checkmark and toast notification. | ✅ **PASSED** |
| **TC-US21-03** | `test_tc_us21_03_deactivate_and_reactivate_flow` | HR clicks "Deactivate Application Link"; verifies status badge reactively updates to "Deactivated (Access Blocked)" with red styling; clicks "Activate Application Link"; verifies status restores to "Active (Accepting Applications)". | ✅ **PASSED** |
| **TC-US21-04** | `test_tc_us21_04_regenerate_token_confirmation_flow` | HR clicks "Regenerate Token"; verifies warning banner appears indicating old links will be revoked; clicks "Confirm"; asserts input field updates with a freshly generated token. | ✅ **PASSED** |
| **TC-US21-05** | `test_tc_us21_05_public_candidate_application_view` | Unauthenticated applicant navigates to `/apply/:token`; asserts page mounts without login prompt; verifies company name, job title, seniority badge, required skills list, and evaluation formula weights (CV% vs Video%). | ✅ **PASSED** |
| **TC-US21-06** | `test_tc_us21_06_public_deactivated_link_error_state` | Applicant accesses deactivated token URL; verifies application error page renders with HTTP 410 indicator, inactive banner, position context, and recruiter contact guidance. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verified

- ✅ **AC 1 — Cryptographic High-Entropy Token Generation:** Utilizes `secrets.token_urlsafe(32)` providing 256 bits of entropy, exceeding security standards and ensuring unguessable URLs.
- ✅ **AC 2 — Public Unauthenticated Candidate View:** Candidates access `/apply/:token` freely without authentication, viewing job details, skills, and CV/Video scoring weights.
- ✅ **AC 3 — 1-Click Clipboard Copy with Feedback:** Modal and room card copy buttons copy the full candidate URL with instant visual "Copied!" feedback and automatic timeout reset.
- ✅ **AC 4 — Link Deactivation & HTTP 410 Gone:** HR can deactivate links on demand. Deactivated links return HTTP 410 Gone with informative UI messaging to prevent unauthorized submissions.
- ✅ **AC 5 — Link Reactivation:** HR can re-enable deactivated links at any time, instantly restoring HTTP 200 access.
- ✅ **AC 6 — Link Regeneration with Invalidation:** Regenerating issues a brand-new 32-byte token and immediately causes old links to return HTTP 404 Not Found.
- ✅ **AC 7 — Strict RBAC & Tenant Isolation:** Only the HR Manager who created the recruitment room can access and manage link configuration endpoints (`IsHRManager` + `created_by` ownership check).

---

## 4. Defects Caught & Resolved During QA

During peer review and testing, 3 defects were identified and resolved in commit `b5d5b72`:

### 🟢 Defect 1: Token Entropy Mismatch (Backend)
- **Description:** `generate_secure_share_token` in `tokens.py` and `save()` in `RecruitmentRoom` defaulted to 16 bytes (~22 characters) instead of the 32 bytes (~43 characters) specified in US-21-T1.
- **Resolution:** Updated default token length in `tokens.py` and `models.py` to `secrets.token_urlsafe(32)`.

### 🟢 Defect 2: Stale `updated_at` Timestamp on Link Updates (Backend)
- **Description:** In `RecruitmentRoomViewSet` actions (`deactivate_link`, `activate_link`, `regenerate_link`), saving with `update_fields=['link_is_active', 'share_token']` bypassed Django's `auto_now=True` timestamp updates.
- **Resolution:** Added `'updated_at'` to `update_fields` across all link mutation actions in `backend/apps/recruitment/views.py`.

### 🟢 Defect 3: Ambiguous Error Code for Closed Rooms (Backend / API)
- **Description:** When an applicant accessed a room with `status == 'CLOSED'`, `PublicApplicationView` fell back to `LINK_DEACTIVATED` instead of a distinct error code.
- **Resolution:** Explicitly added `ROOM_CLOSED` error code in `PublicApplicationView` response when `room.status == 'CLOSED'`.

---

## 5. Test Environment & Artifacts

- **Backend Unit Tests:** [`backend/apps/recruitment/tests/test_shareable_link.py`](file:///f:/CareerFlow/backend/apps/recruitment/tests/test_shareable_link.py) (14/14 passed)
- **Automated UI Test Suite:** [`tests/test_us21_shareable_link_ui.py`](file:///f:/CareerFlow/tests/test_us21_shareable_link_ui.py) (6/6 passed)
- **Markdown Report Location:** [`tests/reports/sprint4_us21_report.md`](file:///f:/CareerFlow/tests/reports/sprint4_us21_report.md)

---

## 6. Final Recommendation

🟢 **APPROVED FOR MERGE INTO `develop`**  
The implementation of US-21 meets all security, functional, and user experience requirements. All 14 backend unit tests pass, and all automated UI test scenarios are verified. Ready for manual review and merge.
