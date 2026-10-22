# Pull Request Guide: US-05 Secure Password Reset

## Quick PR Links
- **Compare & Create PR Link:** [Open PR on GitHub](https://github.com/jubair65/CareerFlow/compare/develop...feat/us-05-password-reset?expand=1)
- **Base Branch:** `develop`
- **Compare Branch:** `feat/us-05-password-reset`
- **Recommended PR Title:** `feat(us-05): Secure Password Reset Workflow with 4-Digit Verification Code`

---

## Copy-Paste PR Template for GitHub

```markdown
## Summary of Changes

Implements **US-05: Secure Password Reset** for Sprint 6. Users can securely reset forgotten passwords through an intuitive 3-step verification wizard using a random 4-digit verification code and cryptographic reset tokens.

### Motivation
- Previously, CareerFlow lacked an account recovery mechanism if users forgot their password.
- Terminal MIME-wrapping issues in local testing made clicking long encoded URLs brittle. We introduced a **4-digit verification code** that prints cleanly in terminal/email, allowing users to verify in-place before updating credentials.

---

## Acceptance Criteria Coverage

| Criterion | Status | Implementation Details |
|---|---|---|
| **AC 1: Request reset with registered email** | Done | `POST /api/auth/password-reset-request/` accepts email, strips/lowercases input, and creates time-limited token/code. |
| **AC 2: Secure, time-limited token/code** | Done | 15-minute TTL enforced via `PasswordResetToken.expires_at`. Both a 4-digit code and SHA-256 token hash are generated. |
| **AC 3: Expired/used tokens rejected** | Done | `validate_and_consume_code` checks `is_used` and `expires_at >= now()`. Marked `is_used=True` immediately upon password change. Replay attempts return `400 Bad Request`. |
| **AC 4: Validated & securely hashed** | Done | Django's `validate_password` enforces length and complexity rules. Password hashed via PBKDF2 with SHA-256 before database persistence. |
| **AC 5: Blind user enumeration protection** | Done | Non-existent emails return identical `200 OK` response with zero tokens or emails created. Prevents attacker account discovery. |
| **AC 6: Old password revocation** | Done | Old password ceases to function immediately upon reset confirmation. All pending tokens for that user are revoked. |

---

## Reviewer Guide & Key Areas for Review

### 1. Backend Security & Token Architecture (`backend/apps/authentication/`)
- [`models.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/backend/apps/authentication/models.py): `PasswordResetToken` stores SHA-256 token hash and 4-digit code. Includes helper methods `verify_code()` (non-destructive check) and `validate_and_consume_code()` (atomic invalidation).
- [`views.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/backend/apps/authentication/views.py):
  - `PasswordResetRequestView`: Emits clean ASCII terminal banner and dispatches email. Suppresses noisy HTML output when using `console.EmailBackend`.
  - `PasswordResetVerifyCodeView`: `POST /api/auth/password-reset-verify-code/` validates the 4-digit code before proceeding to password entry.
  - `PasswordResetConfirmView`: `POST /api/auth/password-reset-confirm/` consumes the token/code and sets the new password.
- [`serializers.py`](file:///d:/Study/3.2/CSE-314/CareerFlow/backend/apps/authentication/serializers.py): Dual-mode support for `(email, code)` or `(uid, token)` ensures full backward compatibility with email links and automated test suites.

### 2. Frontend User Experience (`frontend/src/`)
- [`ForgotPasswordPage.tsx`](file:///d:/Study/3.2/CSE-314/CareerFlow/frontend/src/pages/ForgotPasswordPage.tsx):
  - Step 1: Email entry with validation.
  - Step 2: 4-digit code entry with auto-focus, paste sanitation (strips non-digits), and terminal banner guidance.
  - Step 3: New password with live strength indicator and show/hide eye toggles.
  - Step 4: Success card with direct return to login.
- [`ResetPasswordPage.tsx`](file:///d:/Study/3.2/CSE-314/CareerFlow/frontend/src/pages/ResetPasswordPage.tsx): Seamlessly redirects direct visits or incomplete link visits to the 4-digit verification flow.
- [`api/auth.ts`](file:///d:/Study/3.2/CSE-314/CareerFlow/frontend/src/api/auth.ts): Added `apiPasswordResetRequest`, `apiPasswordResetVerifyCode`, and `apiPasswordResetConfirm`.

---

## Verification & Automated Test Results

- **Unit Tests (`apps.authentication.tests.test_us05_password_reset.py`):**
  - 12/12 tests passing (`Ran 12 tests in 9.108s. OK`).
  - Covers: Token generation, blind enumeration protection, malformed emails, successful resets, replay attacks, expired tokens, tampered tokens, password complexity rules, 4-digit code verification, invalid/expired code rejection, code reset, and code replay rejection.
- **Frontend Typecheck & Build:**
  - `npm run build` completed cleanly in 7.21s with 0 errors.

---

## Notes for Team & Reviewers
- **Maria (Task US-05-T6):** The backend APIs and frontend pages are ready for cross-testing and automated Selenium UI verification.
- **Security Check:** Zero credentials, tokens, or hashes are logged in production mode.
```
