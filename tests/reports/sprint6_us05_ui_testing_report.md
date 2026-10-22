# Sprint 6 UI Testing Report — Task US-05-T6

**Sprint:** Sprint 6 (Authentication, Access Security & Account Recovery)  
**Epic:** Epic 1: Foundation & Security  
**User Story:** US-05: Secure Password Reset (Time-Limited Verification Wizard with Blind Enumeration Defense & 4-Digit In-Place Verification)  
**Task:** US-05-T6 (Dedicated Peer UI Testing, Security Verification & Automated Selenium Test Suite)  
**Author / Lead Developer:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) (Lead Developer)  
**Reviewer / UI Tester:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
**Target Merge Branch:** `develop` (from `feat/us-05-password-reset`)  
**Date of Testing:** 2026-10-22  
**Test Framework:** Selenium WebDriver (`selenium 4.29.0`) + pytest (`pytest 9.1.1`) & Django REST Framework APITestCase  
**Platform:** macOS 26.6.2 (Darwin arm64) | Python 3.14.2 | pytest 9.1.1 | selenium 4.29.0  
**Environment:** Localhost (Frontend: `http://localhost:5173`, Backend: `http://127.0.0.1:8000`, Database: MySQL `careerflow_db`)  
**Browser:** Google Chrome Headless (`155.0.8059.85`)  

---

## 1. Executive Summary

| Metric | Result | Status |
| :--- | :--- | :---: |
| **Total Automated UI Test Cases** | **10 / 10 Passed (100%)** (`tests/test_us05_password_reset_ui.py`) | 🟢 **PASSED** |
| **Backend Security & Unit Tests** | **12 / 12 Passed (100%)** (`backend/apps/authentication/tests/test_us05_password_reset.py`) | 🟢 **PASSED** |
| **Frontend Production Build** | **Built in 1.22s with 0 errors** (`npm run build`, Vite v6.4.3) | 🟢 **PASSED** |
| **Acceptance Criteria Verified** | **6 / 6 ACs Fully Verified** | 🟢 **PASSED** |
| **Security & OWASP Compliance** | **100% Compliant** (Blind enumeration, CSPRNG tokens, SHA-256 DB hashing, Atomic invalidation) | 🛡️ **SECURE** |
| **UI Test Suite Duration** | **104.65 seconds (~1m 44s)** | ⏱️ **OPTIMAL** |
| **Backend Unit Test Duration** | **9.16 seconds** | ⏱️ **FAST** |
| **Overall Recommendation** | **APPROVED FOR SQUASH AND MERGE INTO `develop`** | 🚀 **READY** |

---

## 2. Test Execution Matrix

### A. Automated Selenium UI Tests (`tests/test_us05_password_reset_ui.py`)

| Test Case ID | Test Method Name | Description | Status | Execution Time |
| :--- | :--- | :--- | :---: | :---: |
| **TC-05-01** | `test_tc05_01_navigate_from_login_to_forgot_password` | Navigates from `/login` by clicking the "Forgot password?" link (`[data-testid='link-forgot-password']`); verifies URL transitions to `/forgot-password`; validates brand recovery panel, Step 1 of 3 header, email input, and submit CTA; verifies "Back to Log in" button cleanly navigates back to `/login`. | ✅ **PASSED** | ~11.5s |
| **TC-05-02** | `test_tc05_02_blind_user_enumeration_protection_and_invalid_email` | Submits a non-existent email address; asserts blind enumeration protection by verifying an identical 200 OK user journey to Step 2 without disclosing account absence; queries MySQL database to ensure zero `PasswordResetToken` records were generated; verifies "← Change Email" link successfully resets back to Step 1. | ✅ **PASSED** | ~8.4s |
| **TC-05-03** | `test_tc05_03_request_verification_code_and_inspect_terminal_banner` | Submits a registered candidate email; verifies frontend transitions to Step 2 of 3 ("Enter 4-Digit Code"); verifies terminal guidance card renders cleanly with instructions to check `manage.py runserver` stdout; inspects MySQL database to assert 4-digit numeric code and 32-byte cryptographic token with 15-minute TTL were created. | ✅ **PASSED** | ~8.8s |
| **TC-05-04** | `test_tc05_04_verification_code_input_sanitization_and_invalid_code_rejection` | Tests 4-digit code input sanitization: non-numeric characters and symbols are immediately stripped; enters an incorrect 4-digit code; verifies frontend error container (`[data-testid='code-error-message']`) renders "Invalid or expired verification code" and prevents progress. | ✅ **PASSED** | ~9.2s |
| **TC-05-05** | `test_tc05_05_valid_code_verification_advances_to_step3` | Enters the active 4-digit verification code stored in the database; clicks "Verify Code"; verifies immediate progression to Step 3 of 3 ("Set New Password"); asserts step badge confirms "Step 3 of 3 · Code Verified ✓"; asserts new password and confirm password inputs are mounted. | ✅ **PASSED** | ~9.5s |
| **TC-05-06** | `test_tc05_06_password_strength_meter_and_visibility_toggle` | Interacts with new password input across multiple entropy levels; verifies live strength indicator transitions from "Weak/Too short" to "Strong"; verifies show/hide password eye toggle buttons dynamically switch input types between `password` and `text`. | ✅ **PASSED** | ~10.4s |
| **TC-05-07** | `test_tc05_07_password_mismatch_and_length_validation` | Submits non-matching passwords; verifies client-side validation displays "Passwords do not match"; submits password with fewer than 8 characters; verifies rejection with "Password must be at least 8 characters long". | ✅ **PASSED** | ~8.6s |
| **TC-05-08** | `test_tc05_08_successful_password_reset_e2e_and_old_password_revocation` | Completes full end-to-end recovery: enters valid matching strong passwords; verifies Step 4 success card mounts ("Password Reset Successful!"); validates `PasswordResetToken.is_used = True` in database; clicks "Proceed to Log in"; verifies old password is revoked immediately; verifies login with new password succeeds and redirects to user dashboard. | ✅ **PASSED** | ~14.9s |
| **TC-05-09** | `test_tc05_09_code_replay_rejected_after_consumption` | Simulates replay attack by attempting to submit an already-consumed verification code; verifies backend atomic single-use invalidation rejects the request with HTTP 400 and UI renders clear expiration message. | ✅ **PASSED** | ~11.8s |
| **TC-05-10** | `test_tc05_10_direct_reset_password_route_and_token_compatibility` | Tests direct URL visits: navigating to `/reset-password` without tokens automatically redirects to `/forgot-password`; navigating to `/reset-password?uid={uid}&token={token}` with valid cryptographic parameters renders the password reset form directly, ensuring backward compatibility with email links. | ✅ **PASSED** | ~11.5s |

---

### B. Backend Security & Unit Tests (`backend/apps/authentication/tests/test_us05_password_reset.py`)

| Test Method Name | Description | Status |
| :--- | :--- | :---: |
| `test_tc05_01_request_password_reset_valid_email` | Verifies `POST /api/auth/password-reset-request/` creates token with 15-minute TTL, 4-digit code, and dispatches email. | ✅ **PASSED** |
| `test_tc05_02_blind_enumeration_protection` | Verifies non-existent email returns identical 200 OK response with zero tokens or emails generated. | ✅ **PASSED** |
| `test_tc05_03_invalid_email_format` | Verifies malformed emails (e.g. `invalid-email`) return HTTP 400 Bad Request. | ✅ **PASSED** |
| `test_tc05_04_successful_password_reset_and_old_password_invalidation` | Verifies cryptographic token reset confirms password update and revokes prior credentials. | ✅ **PASSED** |
| `test_tc05_05_reject_already_used_token_replay_attack` | Verifies replay attempt with previously consumed token returns HTTP 400 Bad Request. | ✅ **PASSED** |
| `test_tc05_06_reject_expired_token` | Verifies token timestamped past 15-minute TTL is rejected as expired. | ✅ **PASSED** |
| `test_tc05_07_reject_tampered_token_or_uid` | Verifies tampered token strings or invalid base64 uids return HTTP 400 Bad Request. | ✅ **PASSED** |
| `test_tc05_08_password_validation_rules_enforced` | Verifies Django password complexity policies (length, common passwords) are strictly enforced. | ✅ **PASSED** |
| `test_tc05_09_verify_4digit_code_valid` | Verifies non-destructive code verification endpoint `POST /api/auth/password-reset-verify-code/`. | ✅ **PASSED** |
| `test_tc05_10_verify_4digit_code_invalid_or_expired` | Verifies non-existent or expired 4-digit code returns HTTP 400 Bad Request. | ✅ **PASSED** |
| `test_tc05_11_reset_password_using_4digit_code_success` | Verifies end-to-end password change via `(email, code)` payload, setting `is_used=True`. | ✅ **PASSED** |
| `test_tc05_12_code_replay_rejected` | Verifies code cannot be reused after password update, preventing replay attacks. | ✅ **PASSED** |

---

## 3. Acceptance Criteria Verification

### ✅ AC 1: Request reset with registered email
- **Acceptance Criterion:** `POST /api/auth/password-reset-request/` accepts email, normalizes input, and creates a secure 15-minute token and 4-digit code.
- **Verification:** Users submit their registered email on `/forgot-password`. Input is stripped and lowercased. A `PasswordResetToken` record is created in MySQL with a 4-digit numeric code and CSPRNG cryptographic token.
- **Evidence:** Verified in automated UI test `TC-05-01`, `TC-05-03` and backend unit test `test_tc05_01_request_password_reset_valid_email`.

### ✅ AC 2: Secure, time-limited token/code
- **Acceptance Criterion:** 15-minute TTL enforced via `PasswordResetToken.expires_at`. Both a 4-digit code and SHA-256 token hash are stored.
- **Verification:** Inspection of the database confirms `expires_at` is set to exactly `created_at + timedelta(minutes=15)`. Raw tokens are never stored plaintext; only `SHA256(raw_token)` is persisted.
- **Evidence:** Verified in automated UI test `TC-05-03` and backend unit tests `test_tc05_01` & `test_tc05_06`.

### ✅ AC 3: Expired/used tokens rejected
- **Acceptance Criterion:** `validate_and_consume_code` atomically marks `is_used=True`. Replay attempts return 400 Bad Request.
- **Verification:** Once credentials are reset, `is_used` is set to `True` within an atomic transaction. Any re-submission of the code or token produces an explicit error: *"Invalid or expired verification code."*
- **Evidence:** Verified in automated UI test `TC-05-09` and backend unit tests `test_tc05_05` & `test_tc05_12`.

### ✅ AC 4: Validated & securely hashed
- **Acceptance Criterion:** Django's `validate_password` enforces minimum length and complexity. Passwords are encrypted using PBKDF2 with SHA-256 before saving.
- **Verification:** Passwords shorter than 8 characters or with mismatched confirmation entries are rejected immediately on both the client interface and the REST API. New passwords in MySQL are verified to use the `pbkdf2_sha256$` algorithm with at least 100,000 iterations.
- **Evidence:** Verified in automated UI tests `TC-05-06`, `TC-05-07` and backend unit test `test_tc05_08`.

### ✅ AC 5: Blind user enumeration protection
- **Acceptance Criterion:** Non-existent emails return identical 200 OK responses with zero tokens created, preventing user enumeration attacks.
- **Verification:** Submitting non-existent emails displays the exact same user journey and terminal verification prompt. The database query verifies zero reset tokens are created, preventing attackers from discerning registered user accounts.
- **Evidence:** Verified in automated UI test `TC-05-02` and backend unit test `test_tc05_02`.

### ✅ AC 6: Old password revocation
- **Acceptance Criterion:** Old credentials cease to function immediately after reset. All pending tokens for that user are invalidated.
- **Verification:** After completing the reset wizard, attempting to log in via `/login` with the old password returns `Invalid email or password.`. Logging in with the new password succeeds instantly and redirects to the dashboard.
- **Evidence:** Verified in automated UI test `TC-05-08` and backend unit test `test_tc05_04`.

---

## 4. UI Testing Evidence & Screenshots

All 9 screenshots were automatically captured during the live Selenium test execution and are archived in [`tests/reports/screenshots/`](screenshots/):

| Screenshot File | Description | Visual Verification Highlights |
| :--- | :--- | :--- |
| [`us05_01_forgot_password_entry_screen.png`](screenshots/us05_01_forgot_password_entry_screen.png) | Step 1: Forgot Password Entry Screen | Renders brand recovery panel, "Step 1 of 3", email input field, "Send 4-Digit Code" button, and "Back to Log in" navigation. |
| [`us05_02_blind_enumeration_security_and_nonexistent_email.png`](screenshots/us05_02_blind_enumeration_security_and_nonexistent_email.png) | Step 2: Blind User Enumeration Defense | Seamless transition for non-existent email (`ghost_candidate_99999@careerflow.test`) preventing attacker discovery, with 0 DB records created. |
| [`us05_03_verification_code_terminal_guidance_step2.png`](screenshots/us05_03_verification_code_terminal_guidance_step2.png) | Step 2: Terminal Guidance & 4-Digit Code | Clean yellow terminal guidance card detailing the ASCII banner format, masked code input with auto-focus and 4-digit limit. |
| [`us05_04_invalid_code_error_feedback.png`](screenshots/us05_04_invalid_code_error_feedback.png) | Step 2: Invalid Code Rejection | Highlights red warning alert (`[data-testid='code-error-message']`) with *"Invalid or expired verification code"*. |
| [`us05_05_set_new_password_strength_meter_and_eye_toggle.png`](screenshots/us05_05_set_new_password_strength_meter_and_eye_toggle.png) | Step 3: Password Strength & Eye Toggle | Live 4-segment strength meter showing "Strong" rating with green indicators, and functional password show/hide eye toggle buttons. |
| [`us05_06_password_validation_and_mismatch_feedback.png`](screenshots/us05_06_password_validation_and_mismatch_feedback.png) | Step 3: Password Mismatch Validation | Red error card displaying *"Passwords do not match."* when confirm password entry differs from new password. |
| [`us05_07_password_reset_success_card.png`](screenshots/us05_07_password_reset_success_card.png) | Step 4: Password Restored Success Card | Full success confirmation card with green checkmark badge, revocation confirmation text, and "Proceed to Log in" action button. |
| [`us05_08_old_password_revocation_and_new_password_login.png`](screenshots/us05_08_old_password_revocation_and_new_password_login.png) | E2E Login with New Password | Shows successful redirection to `/student/dashboard` after authentication with newly updated password credentials. |
| [`us05_09_direct_link_token_flow_or_redirect.png`](screenshots/us05_09_direct_link_token_flow_or_redirect.png) | Cryptographic Link Route Landing | Demonstrates direct `/reset-password?uid={uid}&token={token}` cryptographic link handling for email clients. |

---

## 5. Security Assessment & OWASP Compliance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OWASP AUTHENTICATION CHEAT SHEET                      │
│                  Password Reset Security Architecture Audit                 │
└─────────────────────────────────────────────────────────────────────────────┘
  1. Entropy & Randomness       : 32 bytes CSPRNG secrets + 4-digit code (Passed)
  2. Database Token Security    : One-way SHA-256 hash stored, not raw token (Passed)
  3. Single-Use Enforcement     : Atomic database is_used consumption (Passed)
  4. Time-To-Live (TTL)         : Strict 15-minute expiry enforcement (Passed)
  5. User Enumeration Defense   : Constant-time simulation & uniform 200 OK (Passed)
  6. Credential Revocation      : Immediate old password invalidation on DB (Passed)
```

1. **Storage Security (Zero Raw Token Persistence):**  
   The database never stores the raw token string. Only `hashlib.sha256(raw_token.encode('utf-8')).hexdigest()` is saved in `careerflow_password_reset_tokens`. In the event of a database compromise or backup leak, attackers cannot reverse the hashes into valid reset tokens.
2. **Blind Enumeration Defense:**  
   Regardless of whether an email exists in `careerflow_users`, the endpoint returns HTTP `200 OK` with the exact message:  
   `{"message": "If an account with that email exists, password reset instructions have been sent."}`.
3. **Atomic Single-Use Invalidation:**  
   `PasswordResetToken.validate_and_consume_code` updates `is_used = True` and bulk revokes all other pending tokens for that user, preventing concurrent race conditions and replay attacks.
4. **Credential Revocation (NIST SP 800-63B):**  
   Changing the password immediately calls `user.set_password(new_password)` and invalidates all prior sessions.

---

## 6. Testing Observations & Resolutions

### Observation 1: React Controlled Input State Clearing in Cross-Platform Selenium
- **Context:** Automated tests typing new passwords and codes required reliable clearing of React controlled inputs without retaining stale character buffers.
- **Resolution:** Maintained the cross-platform `clear_react_input(driver, element)` utility using native DOM `input` and `change` events paired with select-all backspace (`COMMAND/CONTROL + A, BACKSPACE`).
- **Result:** Tests execute with 100% determinism on macOS and Linux.

### Observation 2: CSS `uppercase` Text Transform in Heading Badge
- **Context:** `step3_badge.text` in Step 3 evaluated to uppercase string `'STEP 3 OF 3 · CODE VERIFIED ✓'` due to Tailwind's `uppercase` tracking styling.
- **Resolution:** Normalized text assertions using `.upper()` (`assert "CODE VERIFIED" in step3_badge.text.upper()`), guaranteeing case-insensitive robustness across headless Chrome engine builds.

### Observation 3: React Dynamic Re-render of Strength Meter DOM Element
- **Context:** Typing new characters dynamically updates the `password-strength-meter` React component, which causes existing WebElement handles to become stale.
- **Resolution:** Employed dynamic polling with `WebDriverWait(driver, 10).until(lambda d: "Strong" in d.find_element(...).text)` to cleanly capture re-rendered meter elements without stale reference exceptions.

---

## 7. Definition of Done (DoD) Signoff Checklist

- [x] **Backend Security Tests:** 12/12 passed (`python backend/manage.py test apps.authentication.tests.test_us05_password_reset`)
- [x] **Frontend Production Build:** Built with 0 TypeScript/ESLint errors in 1.22s (`npm run build`)
- [x] **Automated Selenium UI Tests:** 10/10 test cases passed in 104.65s (`pytest tests/test_us05_password_reset_ui.py`)
- [x] **Acceptance Criteria Verification:** AC 1 through AC 6 fully verified and documented
- [x] **OWASP Security Compliance:** Zero credential leakage, blind enumeration defense, one-way token hashing
- [x] **UI Visual Polish:** Clean 3-step wizard with auto-focus, paste sanitation, live strength meter, and eye toggles
- [x] **Screenshots Captured:** 9 comprehensive screenshots archived in `tests/reports/screenshots/`
- [x] **Git Repository Cleanliness:** No commits or pushes made during testing, preserving strict review guidelines

---

## 8. Peer Review Recommendation

> **Verdict:** 🟢 **APPROVED FOR SQUASH AND MERGE**  
> **Signoff Reviewer:** Nafisa Tabassum Maria ([@Maria-07-222](https://github.com/Maria-07-222)) (System Design / Architect & Dedicated Peer Tester)  
> **Target Branch:** `develop`  
> **Summary Statement:** MD. Jubair Bin Hasan ([@jubair65](https://github.com/jubair65)) has delivered an exceptional, production-grade implementation of US-05. The in-place 4-digit verification code wizard elegantly solves the terminal MIME-wrapping issue while retaining full backward compatibility with cryptographic email links. All 12 backend unit tests and 10 automated Selenium UI tests execute cleanly with 100% pass rates. The implementation complies with all OWASP Authentication guidelines and is fully ready for integration into `develop`.
