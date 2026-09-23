import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apps.authentication.models import User
from conftest import FRONTEND_URL, BACKEND_URL, create_user_in_db


class TestUS04PasswordSecurity:
    """
    US-04: Password Security
    Acceptance Criteria:
    ✓ Passwords are securely hashed using bcrypt or similar (PBKDF2-SHA256)
    ✓ Passwords are never exposed in plain text
    ✓ Password strength validation is enforced
    ✓ Passwords are never logged or sent in emails / API responses
    ✓ Encryption standards meet industry best practices
    """

    def test_tc04_01_passwords_securely_hashed_in_database(self):
        """TC-04-01: Passwords in MySQL database are stored using cryptographic PBKDF2/bcrypt hashing, never plain text."""
        raw_password = "SuperSecretPassword2026!#"
        email = "test_hash_check@careerflow.test"
        user = create_user_in_db(email, raw_password, role=User.Role.STUDENT)

        db_user = User.objects.get(id=user.id)
        stored_hash = db_user.password

        # Ensure raw password is NOT stored anywhere in the database field
        assert raw_password not in stored_hash, "CRITICAL: Raw password was stored in the database!"

        # Verify cryptographic algorithm format (PBKDF2 with SHA256 or bcrypt)
        # Format: <algorithm>$<iterations>$<salt>$<hash>
        assert stored_hash.startswith("pbkdf2_sha256$") or stored_hash.startswith("bcrypt$"), \
            f"Password does not use industry standard cryptographic algorithm: {stored_hash[:20]}"

        parts = stored_hash.split('$')
        assert len(parts) == 4, f"Hash format must have 4 segments (algo, iterations, salt, hash), got {len(parts)}"
        iterations = int(parts[1])
        assert iterations >= 100000, f"PBKDF2 iteration count too low ({iterations}), expected >= 100,000 for NIST compliance"

        # Verify password validation matches
        assert db_user.check_password(raw_password) is True
        assert db_user.check_password("WrongPassword123!") is False

    def test_tc04_02_password_never_exposed_in_api_payloads(self):
        """TC-04-02: User endpoints (/api/auth/me/, /api/auth/login/, /api/auth/register/) NEVER expose password."""
        raw_password = "ApiSafetyPassword2026!"
        email = "test_api_exposure@careerflow.test"
        user = create_user_in_db(email, raw_password, role=User.Role.STUDENT, full_name="Exposed Check")

        # 1. Check /api/auth/login/ response
        login_resp = requests.post(f"{BACKEND_URL}/api/auth/login/", json={
            "email": email,
            "password": raw_password
        })
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "password" not in login_data["user"], "Password found in login user payload!"
        assert "password" not in str(login_data).lower() or "password" not in login_data

        token = login_data["access"]

        # 2. Check /api/auth/me/ response
        me_resp = requests.get(f"{BACKEND_URL}/api/auth/me/", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert "password" not in me_data, "Password found in current user payload (/api/auth/me/)!"

        # 3. Check /api/auth/register/ response
        new_email = "test_api_reg_exposure@careerflow.test"
        reg_resp = requests.post(f"{BACKEND_URL}/api/auth/register/", json={
            "email": new_email,
            "password": raw_password,
            "confirm_password": raw_password,
            "full_name": "Reg Exposure Check",
            "role": "STUDENT"
        })
        assert reg_resp.status_code == 201
        reg_data = reg_resp.json()
        assert "password" not in reg_data["user"], "Password found in registration user payload!"

    def test_tc04_03_ui_password_strength_meter_dynamically_evaluates(self, driver):
        """TC-04-03: UI password strength meter updates strength label and criteria checkmarks in real-time."""
        driver.get(f"{FRONTEND_URL}/register")

        wait = WebDriverWait(driver, 10)
        pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-register-password']")))

        # Test Level 1: Weak (only short letters)
        pass_input.clear()
        pass_input.send_keys("abc")
        meter = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='password-strength-meter']")))
        assert "weak" in meter.text.lower() or "too short" in meter.text.lower()

        # Test Level 2: Fair (8+ chars and uppercase)
        pass_input.clear()
        pass_input.send_keys("Abcdefgh")
        assert "8+ chars" in meter.text
        assert "fair" in meter.text.lower()

        # Test Level 3: Good (8+ chars, uppercase, number)
        pass_input.clear()
        pass_input.send_keys("Abcdefgh1")
        assert "good" in meter.text.lower()

        # Test Level 4: Strong (8+ chars, uppercase, number, symbol)
        pass_input.clear()
        pass_input.send_keys("Abcdefgh1!")
        assert "strong" in meter.text.lower()

    def test_tc04_04_backend_password_validators_enforcement(self):
        """TC-04-04: Backend Django AUTH_PASSWORD_VALIDATORS reject short or purely numeric passwords."""
        # 1. Short password (< 8 chars)
        resp1 = requests.post(f"{BACKEND_URL}/api/auth/register/", json={
            "email": "test_weak1@careerflow.test",
            "password": "pass",
            "confirm_password": "pass",
            "full_name": "Weak Pass User",
            "role": "STUDENT"
        })
        assert resp1.status_code == 400
        assert "password" in resp1.json().get("errors", {})

        # 2. Entirely numeric password
        resp2 = requests.post(f"{BACKEND_URL}/api/auth/register/", json={
            "email": "test_weak2@careerflow.test",
            "password": "1234567890",
            "confirm_password": "1234567890",
            "full_name": "Numeric Pass User",
            "role": "STUDENT"
        })
        assert resp2.status_code == 400
        assert "password" in resp2.json().get("errors", {})
