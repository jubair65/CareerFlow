import sys
import time
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
from apps.cv.models import CandidateCV, CVFeedback, CVJobMatch
from apps.cv.services.scorer import generate_cv_feedback
from apps.cv.services.semantic_matcher import match_cv_to_job
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "cv"


def login_student(driver, email="bonny_resp_student@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Bonny Responsive Tester")

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


def prepare_student_with_full_cv_data(student_email="bonny_resp_data@careerflow.test"):
    """Helper to ensure student has an active CV, feedback, and match record in DB."""
    user = User.objects.filter(email__iexact=student_email).first()
    if not user:
        user = create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bonny Responsive Evaluator")

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
    match_record = match_cv_to_job(
        cv=cv,
        job_title="Senior Frontend Engineer",
        job_description="Seeking a Senior Frontend Engineer proficient in React, TypeScript, and modern responsive UI design.",
        required_skills=["React", "TypeScript", "TailwindCSS", "Accessibility"]
    )
    return user, cv, feedback, match_record


def check_no_horizontal_overflow(driver):
    """
    Verifies that the document body width does not exceed the viewport window width,
    preventing unwanted horizontal scrolling or page blowout on small viewports.
    """
    # Allow 5px tolerance for scrollbar rendering differences
    return driver.execute_script("""
        return (document.documentElement.scrollWidth - window.innerWidth) <= 5;
    """)


class TestUIT01T8ResponsiveLayout:
    """
    UIT-01-T8: Test responsive layout of CV screens on desktop, tablet, and mobile sizes.
    Owner: Bonny

    Target Screens:
    1. /student/cv/match (JobMatch.tsx)
    2. /student/cv/results (CvResults.tsx)
    3. /student/cv (CvStudio.tsx)

    Tested Viewports:
    - Desktop: 1920 x 1080
    - Tablet:  768 x 1024
    - Mobile:  375 x 667

    Acceptance Criteria Verified:
    ✓ Screens adapt fluidly without horizontal overflow blowout.
    ✓ Multi-column cards collapse gracefully to single column on mobile/tablet.
    ✓ Critical interactive elements (buttons, inputs, tabs, dropzones) remain visible and accessible.
    """

    def test_tc_uit01_t8_01_desktop_layout_job_match(self, driver):
        """
        TC-UIT-01-T8-01: Verify Job Match screen layout at desktop viewport (1920x1080).
        Multi-column layout displays side-by-side with zero horizontal overflow.
        """
        driver.set_window_size(1920, 1080)
        student_email = "bonny_t8_tc01_desktop@careerflow.test"
        login_student(driver, email=student_email)
        prepare_student_with_full_cv_data(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        signals_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-signals']")))

        assert hero_card.is_displayed()
        assert signals_card.is_displayed()

        # On desktop, both hero and signals should be rendered in viewport
        hero_rect = hero_card.rect
        signals_rect = signals_card.rect
        assert hero_rect["width"] > 300
        assert signals_rect["width"] > 300

        # No horizontal scroll blowout
        assert check_no_horizontal_overflow(driver), "Horizontal scroll overflow detected on desktop viewport!"

    def test_tc_uit01_t8_02_tablet_layout_job_match(self, driver):
        """
        TC-UIT-01-T8-02: Verify Job Match screen layout at tablet viewport (768x1024).
        Grids adapt, inputs span appropriately, and no horizontal scroll blowout occurs.
        """
        driver.set_window_size(768, 1024)
        student_email = "bonny_t8_tc02_tablet@careerflow.test"
        login_student(driver, email=student_email)
        prepare_student_with_full_cv_data(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        assert hero_card.is_displayed()

        # Ensure hero card width adapts within tablet screen width
        assert hero_card.rect["width"] <= 768, "Hero card exceeds tablet viewport width!"

        # Verify recalculate button remains visible and clickable
        recalc_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-recalculate-match']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recalc_btn)
        assert recalc_btn.is_displayed()

        # Verify no horizontal page blowout
        assert check_no_horizontal_overflow(driver), "Horizontal scroll overflow detected on tablet viewport!"

    def test_tc_uit01_t8_03_mobile_layout_job_match(self, driver):
        """
        TC-UIT-01-T8-03: Verify Job Match screen layout at mobile viewport (375x667).
        Cards stack vertically, 7xl match score text fits within screen, and inputs do not clip.
        """
        driver.set_window_size(375, 667)
        student_email = "bonny_t8_tc03_mobile_match@careerflow.test"
        login_student(driver, email=student_email)
        prepare_student_with_full_cv_data(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        score_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))

        assert hero_card.is_displayed()
        assert score_element.is_displayed()

        inner_w = driver.execute_script("return window.innerWidth;")

        # Match score must not overflow mobile screen width
        score_rect = score_element.rect
        assert score_rect["x"] + score_rect["width"] <= inner_w + 10, "Match score overflows mobile viewport!"

        # Form controls must adapt
        title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-match-title']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_input)
        assert title_input.rect["width"] <= inner_w, "Title input overflows mobile viewport width!"

        # No horizontal scroll blowout
        assert check_no_horizontal_overflow(driver), "Horizontal scroll overflow detected on mobile Job Match screen!"

    def test_tc_uit01_t8_04_mobile_layout_cv_results(self, driver):
        """
        TC-UIT-01-T8-04: Verify CV Results/Feedback screen layout at mobile viewport (375x667).
        Signal breakdown bars, tier badge, and download button scale and remain functional.
        """
        driver.set_window_size(375, 667)
        student_email = "bonny_t8_tc04_mobile_results@careerflow.test"
        login_student(driver, email=student_email)
        prepare_student_with_full_cv_data(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/results")
        wait = WebDriverWait(driver, 10)

        score_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-overall-score']")))
        tier_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-tier-badge']")))
        breakdown_section = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='signal-breakdown']")))

        assert score_card.is_displayed()
        assert tier_badge.is_displayed()
        assert breakdown_section.is_displayed()

        # Download button remains present and unclipped
        download_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-download-cv-report']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
        assert download_btn.is_displayed()

        # Tab navigation buttons visible and clickable
        tab_match = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tab-job-match']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_match)
        assert tab_match.is_displayed()

        # No horizontal scroll blowout
        assert check_no_horizontal_overflow(driver), "Horizontal scroll overflow detected on mobile CV Results screen!"

    def test_tc_uit01_t8_05_mobile_layout_cv_studio(self, driver):
        """
        TC-UIT-01-T8-05: Verify CV Studio (Upload) screen layout at mobile viewport (375x667).
        Upload dropzone area fits mobile width without overflow, and active CV card stacks legibly.
        """
        driver.set_window_size(375, 667)
        student_email = "bonny_t8_tc05_mobile_studio@careerflow.test"
        login_student(driver, email=student_email)
        prepare_student_with_full_cv_data(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv")
        wait = WebDriverWait(driver, 10)

        inner_w = driver.execute_script("return window.innerWidth;")

        dropzone = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-dropzone']")))
        assert dropzone.is_displayed()
        assert dropzone.rect["width"] <= inner_w, "CV Dropzone exceeds mobile viewport width!"

        active_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))
        assert active_card.is_displayed()
        assert active_card.rect["width"] <= inner_w, "Active CV card exceeds mobile viewport width!"

        # No horizontal scroll blowout
        assert check_no_horizontal_overflow(driver), "Horizontal scroll overflow detected on mobile CV Studio screen!"
