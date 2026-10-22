import hashlib
from datetime import timedelta
from django.core import mail
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User, PasswordResetToken


class PasswordResetTests(APITestCase):
    """
    US-05: Secure Password Reset
    Tests covering all 6 Acceptance Criteria:
    ✓ AC 1: User can request a password reset using registered email
    ✓ AC 2: A secure, time-limited reset link or token is sent by email
    ✓ AC 3: Expired, invalid or already-used reset tokens are rejected
    ✓ AC 4: New password is validated and securely hashed before saving
    ✓ AC 5: Responses do not reveal whether an email is registered (blind enumeration)
    ✓ AC 6: Old password stops working after a successful reset
    """

    def setUp(self):
        self.initial_password = "InitialPassword123!"
        self.user = User.objects.create_user(
            username="reset_candidate",
            email="candidate_reset@careerflow.test",
            password=self.initial_password,
            full_name="Candidate Reset",
            role=User.Role.STUDENT
        )
        self.request_url = "/api/auth/password-reset-request/"
        self.confirm_url = "/api/auth/password-reset-confirm/"
        self.verify_code_url = "/api/auth/password-reset-verify-code/"

    def test_tc05_01_request_password_reset_valid_email(self):
        """AC 1 & 2: User requests password reset; secure 15-minute token generated and email dispatched."""
        mail.outbox = []
        response = self.client.post(self.request_url, {"email": self.user.email}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Check DB token creation
        token_entry = PasswordResetToken.objects.filter(user=self.user, is_used=False).first()
        self.assertIsNotNone(token_entry)
        self.assertTrue(token_entry.is_active)
        self.assertGreater(token_entry.expires_at, timezone.now())
        self.assertEqual(len(token_entry.code), 4)

        # Check email sent with 4-digit code
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("Reset Your CareerFlow Password", sent_email.subject)
        self.assertIn(self.user.email, sent_email.to)
        self.assertIn("verification code", sent_email.body.lower())
        self.assertIn(token_entry.code, sent_email.body)

    def test_tc05_02_blind_enumeration_protection(self):
        """AC 5: Non-existent email returns identical 200 OK response with zero tokens or emails created."""
        mail.outbox = []
        ghost_email = "non_existent_ghost_999@careerflow.test"
        response = self.client.post(self.request_url, {"email": ghost_email}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_msg = "If an account with that email exists, password reset instructions have been sent."
        self.assertEqual(response.data["message"], expected_msg)

        # Verify no email was dispatched and no token was created
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(PasswordResetToken.objects.filter(user__email=ghost_email).exists())

    def test_tc05_03_invalid_email_format(self):
        """Rejects malformed email with 400 Bad Request."""
        response = self.client.post(self.request_url, {"email": "invalid-email-format"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc05_04_successful_password_reset_and_old_password_invalidation(self):
        """AC 3, 4 & 6: Successful password reset securely updates credentials and immediately revokes old password."""
        raw_token = PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        new_password = "NewSecurePass2026!#"

        payload = {
            "uid": uidb64,
            "token": raw_token,
            "new_password": new_password,
            "confirm_password": new_password
        }
        response = self.client.post(self.confirm_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("successfully reset", response.data["message"])

        # AC 6: Verify old password stops working immediately
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.initial_password))
        self.assertTrue(self.user.check_password(new_password))

        # AC 3: Verify token is consumed
        token_entry = PasswordResetToken.objects.filter(user=self.user).first()
        self.assertTrue(token_entry.is_used)

    def test_tc05_05_reject_already_used_token_replay_attack(self):
        """AC 3: Replay attack with an already-used token is rejected with 400 Bad Request."""
        raw_token = PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        new_password = "NewPasswordFirst123!"

        # First consumption (succeeds)
        res1 = self.client.post(self.confirm_url, {
            "uid": uidb64,
            "token": raw_token,
            "new_password": new_password,
            "confirm_password": new_password
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Replay attempt with same token (must fail)
        res2 = self.client.post(self.confirm_url, {
            "uid": uidb64,
            "token": raw_token,
            "new_password": "AnotherNewPassword123!",
            "confirm_password": "AnotherNewPassword123!"
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid or has expired", res2.data["error"])

    def test_tc05_06_reject_expired_token(self):
        """AC 3: A token that has passed the 15-minute window is rejected."""
        raw_token = PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=-5)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        payload = {
            "uid": uidb64,
            "token": raw_token,
            "new_password": "ValidNewPassword2026!",
            "confirm_password": "ValidNewPassword2026!"
        }
        response = self.client.post(self.confirm_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid or has expired", response.data["error"])

    def test_tc05_07_reject_tampered_token_or_uid(self):
        """AC 3: Forged or corrupted tokens/UIDs are rejected."""
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        # Tampered token
        res1 = self.client.post(self.confirm_url, {
            "uid": uidb64,
            "token": "forged_non_existent_token_12345",
            "new_password": "ValidPassword2026!",
            "confirm_password": "ValidPassword2026!"
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Tampered UID
        res2 = self.client.post(self.confirm_url, {
            "uid": "invalid-uid-base64",
            "token": "some_token",
            "new_password": "ValidPassword2026!",
            "confirm_password": "ValidPassword2026!"
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc05_08_password_validation_rules_enforced(self):
        """AC 4: Weak passwords or mismatched confirmations are rejected."""
        raw_token = PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

        # Mismatch
        res_mismatch = self.client.post(self.confirm_url, {
            "uid": uidb64,
            "token": raw_token,
            "new_password": "ValidPassword2026!",
            "confirm_password": "DifferentPassword2026!"
        }, format="json")
        self.assertEqual(res_mismatch.status_code, status.HTTP_400_BAD_REQUEST)

        # Too short (Django default minimum length is 8)
        res_short = self.client.post(self.confirm_url, {
            "uid": uidb64,
            "token": raw_token,
            "new_password": "short",
            "confirm_password": "short"
        }, format="json")
        self.assertEqual(res_short.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc05_09_verify_4digit_code_valid(self):
        """US-05: 4-digit verification code validates successfully before changing password."""
        PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        token_entry = PasswordResetToken.objects.filter(user=self.user, is_used=False).first()

        response = self.client.post(self.verify_code_url, {
            "email": self.user.email,
            "code": token_entry.code
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("valid"))
        self.assertIn("verified successfully", response.data.get("message"))

    def test_tc05_10_verify_4digit_code_invalid_or_expired(self):
        """US-05: Non-matching or expired 4-digit code is rejected with 400 Bad Request."""
        PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=-10)  # already expired
        token_entry = PasswordResetToken.objects.filter(user=self.user).first()

        # Expired code
        res_expired = self.client.post(self.verify_code_url, {
            "email": self.user.email,
            "code": token_entry.code
        }, format="json")
        self.assertEqual(res_expired.status_code, status.HTTP_400_BAD_REQUEST)

        # Non-matching wrong code
        res_wrong = self.client.post(self.verify_code_url, {
            "email": self.user.email,
            "code": "0000"
        }, format="json")
        self.assertEqual(res_wrong.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tc05_11_reset_password_using_4digit_code_success(self):
        """US-05: User successfully resets password using 4-digit code pasted from terminal/email."""
        PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        token_entry = PasswordResetToken.objects.filter(user=self.user, is_used=False).first()
        new_password = "SecureCodePass2026!#"

        payload = {
            "email": self.user.email,
            "code": token_entry.code,
            "new_password": new_password,
            "confirm_password": new_password
        }
        response = self.client.post(self.confirm_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("successfully reset", response.data.get("message"))

        # Verify old password stops working immediately and new password works
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.initial_password))
        self.assertTrue(self.user.check_password(new_password))

        # Verify code is marked as used
        token_entry.refresh_from_db()
        self.assertTrue(token_entry.is_used)

    def test_tc05_12_code_replay_rejected(self):
        """US-05: Once 4-digit code is used to reset password, it cannot be reused."""
        PasswordResetToken.create_token_for_user(self.user, lifetime_minutes=15)
        token_entry = PasswordResetToken.objects.filter(user=self.user, is_used=False).first()
        new_password = "FirstCodePass2026!#"

        # First consumption
        res1 = self.client.post(self.confirm_url, {
            "email": self.user.email,
            "code": token_entry.code,
            "new_password": new_password,
            "confirm_password": new_password
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Replay attempt
        res2 = self.client.post(self.confirm_url, {
            "email": self.user.email,
            "code": token_entry.code,
            "new_password": "SecondCodePass2026!#",
            "confirm_password": "SecondCodePass2026!#"
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

