# CareerFlow — Sprint 6 Security Architecture Specification
## US-05: Secure Time-Limited Password Reset Flow with Blind Enumeration Protection

**Author / Lead Developer:** MD. Jubair Bin Hasan (SD)  
**Epic:** Epic 1: Foundation & Security  
**Target Story:** US-05 (`feat/us-05-password-reset`)  
**Task ID:** `US-05-T1` — Design secure time-limited password reset flow  
**Status:** Architecture Completed & Approved  

---

## 1. Executive Summary & Objective

In CareerFlow, users with sensitive roles—including **Students** (submitting CVs and AI video presentations), **HR Managers** (evaluating candidate shortlists), and **Agency Admins** (managing multi-tenant client companies)—must be able to recover account access securely if credentials are forgotten.

A vulnerable password reset mechanism is one of the most common vectors for account takeover and user enumeration. **US-05** defines an enterprise-grade, cryptographically secure password reset flow adhering to OWASP Authentication Cheat Sheet guidelines.

### Core Security Guarantees
1. **Blind Enumeration Protection:** The system always returns an identical, generic HTTP 200 response regardless of whether the requested email exists in the database.
2. **Cryptographic Entropy:** Reset tokens are generated using OS-level cryptographically secure pseudo-random number generators (CSPRNG, 32 bytes URL-safe base64, providing 256 bits of entropy).
3. **Storage Security (One-Way Hashing):** Raw tokens are never stored plaintext in the database. The database stores only the SHA-256 hash of the token, preventing token harvesting even in the event of a database leak.
4. **Time-Limited Expiry:** Tokens are valid for exactly **15 minutes** (900 seconds) from creation.
5. **Single-Use Enforcement:** Once consumed to reset a password, the token is flagged as `is_used = True`, and all outstanding tokens for that user are revoked.
6. **Immediate Old Password Invalidation:** Changing the password immediately hashes the new password with Django's PBKDF2/Argon2 implementation, terminating prior authentication sessions.

---

## 2. Threat Modeling & OWASP Mitigation Matrix

| Threat Vector | Attack Scenario | CareerFlow Mitigation Strategy |
| :--- | :--- | :--- |
| **User Enumeration (Timing & Response)** | Attacker submits emails to discover if an executive or candidate has an account on CareerFlow based on error messages or response duration. | **Uniform Response:** Always respond with HTTP `200 OK` and payload `{"message": "If an account with that email exists, password reset instructions have been sent."}`. Constant-time processing ensures no timing disparity. |
| **Token Interception / Leaked DB** | Attacker dumps the database or accesses backup snapshots to obtain active reset links. | **One-Way Hashing:** Raw tokens are emailed directly to the user. The database only stores `SHA256(raw_token)`. Leaked database entries cannot be converted into usable reset tokens. |
| **Brute-Force Token Guessing** | Attacker repeatedly guesses 6-digit or weak reset codes. | **High Entropy Tokens:** 32-byte URL-safe base64 tokens (~43 alphanumeric characters) with 256 bits of entropy. Brute-force space is $2^{256}$, rendering guessing computationally infeasible. |
| **Token Replay Attacks** | Attacker or unauthorized network observer intercepts an old token or uses browser back-button to reset password again. | **Atomic Single-Use State:** A token is marked `is_used=True` in an atomic database transaction. Any subsequent attempt to use the same token is rejected with `400 Bad Request`. |
| **Token Lingering / Stale Links** | User leaves an unused reset link in their email inbox for weeks; attacker accesses inbox later. | **Strict 15-Minute Expiry:** Query strictly filters `expires_at >= timezone.now()`. Expired tokens are immediately rejected. |
| **Denial of Service / Mail Flooding** | Attacker loops reset requests for victim's email to flood inbox or exhaust SMTP quotas. | **Throttling & Cooldown:** Enforce a 60-second cooldown per user/email and per-IP rate-limiting. |

---

## 3. Cryptographic Token Lifecycle & State Diagram

```
                 [ User submits email ]
                           │
                           ▼
          ┌───────────────────────────────────┐
          │  Check if User exists in DB       │
          └─────────────────┬─────────────────┘
                            │
              ┌─────────────┴─────────────┐
        Exists│                           │Does Not Exist
              ▼                           ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Generate 32-byte CSPRNG token │   │ Simulate constant-time hash   │
│ Compute SHA-256(raw_token)    │   │ (Prevent timing side-channel) │
│ Save PasswordResetToken in DB │   └───────────────┬───────────────┘
│ with expires_at = now + 15m   │                   │
│ Send HTML email with link     │                   │
└─────────────┬─────────────────┘                   │
              │                                     │
              └─────────────┬───────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Return HTTP 200 (Generic) │
              └───────────────────────────┘
                            │
                            ▼
           [ User clicks email link in inbox ]
                            │
                            ▼
              ┌───────────────────────────┐
              │ Enter new password on UI  │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ Submit uidb64 + raw_token │
              │ + new_password to API     │
              └─────────────┬─────────────┘
                            │
                            ▼
          ┌───────────────────────────────────┐
          │ Validate:                         │
          │ 1. uidb64 decodes to valid User?  │
          │ 2. SHA256(raw_token) exists in DB?│
          │ 3. is_used == False?              │
          │ 4. expires_at >= timezone.now()?  │
          │ 5. new_password passes validator? │
          └─────────────────┬─────────────────┘
                            │
              ┌─────────────┴─────────────┐
         Valid│                           │Invalid / Expired / Used
              ▼                           ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ • Set is_used = True          │   │ Return HTTP 400 Bad Request   │
│ • Revoke other user tokens    │   │ ("Invalid or expired token.") │
│ • user.set_password(new_pass) │   └───────────────────────────────┘
│ • user.save()                 │
│ • Return HTTP 200 OK          │
└───────────────────────────────┘
```

---

## 4. Database Schema Specification: `PasswordResetToken`

The dedicated model will be registered in `backend/apps/authentication/models.py`:

```python
class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text="User requesting the password reset"
    )
    token_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of the raw reset token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when reset was requested"
    )
    expires_at = models.DateTimeField(
        help_text="Exact expiry timestamp (created_at + 15 minutes)"
    )
    is_used = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True once the token has been consumed"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the requester for security auditing"
    )

    class Meta:
        db_table = 'careerflow_password_reset_tokens'
        ordering = ['-created_at']
```

### Key Model Methods
- `create_token_for_user(user, ip_address=None, lifetime_minutes=15) -> str`:
  Generates a 32-byte URL-safe string (`secrets.token_urlsafe(32)`), stores `token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()`, and returns the `raw_token` for one-time transmission via email.
- `validate_and_consume_token(user, raw_token) -> bool`:
  Computes SHA-256 of `raw_token`, queries the DB for `user=user, token_hash=hash, is_used=False, expires_at__gte=now`. If matched, marks `is_used=True`, invalidates any other outstanding tokens for the user, and returns `True`.

---

## 5. REST API Interface Specification

### 5.1 Endpoint 1: Request Password Reset
- **URL:** `POST /api/auth/password-reset-request/`
- **Permissions:** `AllowAny`
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "email": "candidate@example.com"
}
```
- **Responses:**
  - `200 OK` (Always returned, regardless of user existence):
  ```json
  {
    "message": "If an account with that email exists, password reset instructions have been sent."
  }
  ```
  - `400 Bad Request` (Malformed email format):
  ```json
  {
    "error": "Enter a valid email address."
  }
  ```

---

### 5.2 Endpoint 2: Confirm Password Reset
- **URL:** `POST /api/auth/password-reset-confirm/`
- **Permissions:** `AllowAny`
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "uid": "MTI",
  "token": "dGhpcy1pcy1hLXNlY3VyZS10b2tlbi0zMi1ieXRlcw",
  "new_password": "NewSecurePassword123!",
  "confirm_password": "NewSecurePassword123!"
}
```
- **Responses:**
  - `200 OK` (Success):
  ```json
  {
    "message": "Password has been successfully reset. You may now log in with your new credentials."
  }
  ```
  - `400 Bad Request` (Invalid/Expired/Used Token):
  ```json
  {
    "error": "The password reset link is invalid or has expired. Please request a new one."
  }
  ```
  - `400 Bad Request` (Password Validation Failure):
  ```json
  {
    "error": "This password is too common / Passwords do not match / Must contain at least 8 characters."
  }
  ```

---

## 6. Frontend URL Structure & User Experience Flow

- **Forgot Password Initiation:**
  - Route: `/forgot-password` (`frontend/src/pages/ForgotPasswordPage.tsx`)
  - Form: Clean email input field with submit button (`"Send Reset Instructions"`).
  - Post-submit: Replaced by success state: *"Check your email for a reset link. If you don't see it, check spam."*
- **Reset Password Landing:**
  - Route: `/reset-password?uid={uid}&token={token}` (`frontend/src/pages/ResetPasswordPage.tsx`)
  - Auto-reads `uid` and `token` from URL search parameters.
  - Form: `New Password` + `Confirm New Password` inputs with password strength indicator and show/hide eye toggle buttons.
  - Post-submit: Success modal with countdown redirecting to `/login`.

---

## 7. Verification & Acceptance Checklist for US-05

- [x] **US-05-T1:** Cryptographic design & threat modeling documented.
- [ ] **US-05-T2:** Request API with blind enumeration protection implemented.
- [ ] **US-05-T3:** Reset confirmation API with token consumption and hashing implemented.
- [ ] **US-05-T4:** Frontend Forgot Password and Reset Password pages built.
- [ ] **US-05-T5:** Responsive HTML email template integrated with SMTP/console backend.
- [ ] **US-05-T6:** Dedicated cross-testing conducted by Nafisa Tabassum Maria.
- [ ] **US-05-T7:** Unit test suite covering security edge cases created and green.
