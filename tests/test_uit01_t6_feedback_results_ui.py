import sys
import time
import re
from pathlib import Path
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.core.files.base import ContentFile

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from apps.authentication.models import User
from apps.cv.models import CandidateCV, ParsedCV, CVFeedback
from apps.cv.services.scorer import generate_cv_feedback
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "cv"


def login_student(driver, email="maria_feedback_student@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Maria QA Tester")

    driver.get(f"{FRONTEND_URL}/login")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']")

    email_input.clear()
    email_input.send_keys(email)
    pass_input.clear()
    pass_input.send_keys(password)
    submit_btn.click()

    wait.until(EC.url_contains("/student/dashboard"))
    return user


def prepare_candidate_with_cv(student_email="test_feedback_cv@careerflow.test"):
    """Helper to set up a candidate with a valid CV and feedback in database."""
    user = User.objects.filter(email__iexact=student_email).first()
    if not user:
        user = create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Maria QA Evaluator")
    pdf_path = FIXTURES_DIR / "valid_sample.pdf"
    assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

    with open(pdf_path, "rb") as f:
        cv = CandidateCV.objects.create(
            user=user,
            file=ContentFile(f.read(), name="valid_sample.pdf"),
            original_filename="valid_sample.pdf",
            file_size=pdf_path.stat().st_size,
            file_type="pdf",
            is_active=True
        )

    feedback = generate_cv_feedback(cv)
    return user, cv, feedback


class TestUIT01T6FeedbackResultsUI:
    """
    UIT-01-T6: Test CV feedback results UI (formatting, clarity, keyword strength display).
    Owner: Maria
    Target Page: frontend/src/pages/CvResults.tsx (/student/cv/results)

    Standard Test IDs Verified:
    ✓ data-testid="cv-overall-score"
    ✓ data-testid="score-tier-badge"
    ✓ data-testid="signal-breakdown"
    ✓ data-testid="extracted-skills-list"
    ✓ data-testid="card-actionable-suggestions"
    ✓ data-testid="button-download-cv-report"

    Test Assertions:
    1. Score value is an integer between 0 and 100.
    2. All 5 signal breakdown bars (Formatting, Clarity, Keyword Strength, Experience, Education) render with valid widths (0–100%).
    3. At least 3 distinct actionable suggestion callouts are displayed.
    4. Extracted skills list renders parsed technical and domain skills.
    5. Clicking button-download-cv-report triggers download of careerflow-cv-report.txt.
    """

    def test_tc_uit01_t6_01_overall_score_and_tier_badge(self, driver):
        """
        TC-UIT-01-T6-01: Verify overall score displays as an integer (0-100) and tier badge renders correctly.
        """
        student_email = "maria_tc01_score@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        # 1. Verify cv-overall-score element
        score_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-overall-score']"))
        )
        assert score_element.is_displayed()
        score_text = score_element.text.strip()
        assert score_text.isdigit(), f"Overall score '{score_text}' is not a valid integer!"
        score_value = int(score_text)
        assert 0 <= score_value <= 100, f"Overall score {score_value} out of range [0, 100]!"

        # 2. Verify score-tier-badge
        tier_badge = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-tier-badge']"))
        )
        assert tier_badge.is_displayed()
        valid_tiers = ["Strong alignment", "Good potential", "Needs revision"]
        assert any(tier in tier_badge.text for tier in valid_tiers), f"Unexpected tier badge text: {tier_badge.text}"

    def test_tc_uit01_t6_02_signal_breakdown_bars_render_valid_widths(self, driver):
        """
        TC-UIT-01-T6-02: Verify all 5 signal breakdown bars render with valid percentage widths (0-100%).
        """
        student_email = "maria_tc02_signals@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        # Verify signal breakdown section
        breakdown_section = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='signal-breakdown']"))
        )
        assert breakdown_section.is_displayed()

        # The 5 signal keys
        signals = [
            ("keyword", "[data-testid='signal-keyword-strength']"),
            ("clarity", "[data-testid='signal-clarity-impact']"),
            ("formatting", "[data-testid='signal-formatting']"),
            ("experience", "[data-testid='signal-experience']"),
            ("education", "[data-testid='signal-education']"),
        ]

        width_regex = re.compile(r"width:\s*(\d+(?:\.\d+)?)%")

        for signal_name, selector in signals:
            signal_container = breakdown_section.find_element(By.CSS_SELECTOR, selector)
            assert signal_container.is_displayed(), f"Signal '{signal_name}' is not displayed!"

            # Find progress bar within this signal container
            progress_bar = signal_container.find_element(By.CSS_SELECTOR, ".h-full")
            style_attr = progress_bar.get_attribute("style") or ""
            match = width_regex.search(style_attr)
            assert match is not None, f"Progress bar for '{signal_name}' has invalid style: '{style_attr}'"

            width_pct = float(match.group(1))
            assert 0.0 <= width_pct <= 100.0, f"Signal '{signal_name}' width {width_pct}% is out of bounds!"

    def test_tc_uit01_t6_03_actionable_suggestions_display(self, driver):
        """
        TC-UIT-01-T6-03: Verify at least 3 distinct actionable recommendation cards are displayed.
        """
        student_email = "maria_tc03_suggestions@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        suggestions_card = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-actionable-suggestions']"))
        )
        assert suggestions_card.is_displayed()

        # Find suggestion boxes (either by suggestion-item-* testids or within container-suggestions)
        suggestion_elements = suggestions_card.find_elements(By.CSS_SELECTOR, "[data-testid^='suggestion-item-']")
        assert len(suggestion_elements) >= 3, f"Expected at least 3 actionable suggestions, found {len(suggestion_elements)}"

        for idx, item in enumerate(suggestion_elements, start=1):
            assert item.is_displayed()
            text = item.text.strip()
            assert len(text) > 10, f"Suggestion #{idx} is too short or empty: '{text}'"

    def test_tc_uit01_t6_04_extracted_skills_list(self, driver):
        """
        TC-UIT-01-T6-04: Verify extracted technical & domain skills list displays parsed skill badges.
        """
        student_email = "maria_tc04_skills@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        skills_container = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='extracted-skills-list']"))
        )
        assert skills_container.is_displayed()

        badges = skills_container.find_elements(By.CSS_SELECTOR, "[data-testid='skill-badge'], span")
        assert len(badges) >= 1, "No extracted skills badges rendered!"

        badge_texts = [b.text.strip() for b in badges if b.text.strip()]
        assert len(badge_texts) >= 1
        found_skills = " ".join(badge_texts).lower()
        assert any(k in found_skills for k in ["python", "react", "sql", "docker", "javascript", "django"]), \
            f"Expected recognized tech skills in extracted list, found: {badge_texts}"

    def test_tc_uit01_t6_05_download_cv_report(self, driver, tmp_path):
        """
        TC-UIT-01-T6-05: Verify clicking button-download-cv-report triggers report generation/download.
        """
        student_email = "maria_tc05_download@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv(student_email)

        # Configure Chrome to download into tmp_path
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(tmp_path)
        })

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        download_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-download-cv-report']"))
        )
        assert download_btn.is_displayed()

        download_btn.click()

        # Verify success toast notification
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "downloaded successfully" in toast.text.lower()

        # Verify file is downloaded
        time.sleep(1.5)
        downloaded_files = list(tmp_path.glob("careerflow-cv-report*"))
        assert len(downloaded_files) >= 1, f"Expected downloaded report file in {tmp_path}, but found: {list(tmp_path.iterdir())}"

        report_file = downloaded_files[0]
        content = report_file.read_text(encoding="utf-8")
        assert "CAREERFLOW CV FEEDBACK" in content or "OVERALL SCORE" in content
        assert "SIGNAL BREAKDOWN" in content
        assert "ACTIONABLE EDITS" in content
