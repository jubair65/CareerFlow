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


def login_student_browser(driver, email, password="ValidPass2026!", name="Bonny QA Tester"):
    """Helper to log in as candidate/student in any WebDriver instance."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name=name)

    driver.get(f"{FRONTEND_URL}/login")
    wait = WebDriverWait(driver, 12)
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


def prepare_cross_browser_candidate(email="bonny_xbrowser@careerflow.test"):
    """Prepares user with complete CV, feedback, and match record in MySQL."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bonny CrossBrowser Tester")

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
        job_title="Product Designer",
        job_description="Seeking a Product Designer with proven Figma and user research skills.",
        required_skills=["Figma", "Product Strategy", "User Research", "Accessibility", "Systems Thinking"]
    )
    return user, cv, feedback, match_record


class TestUIT01T9CrossBrowserCompatibility:
    """
    UIT-01-T9: Test cross-browser compatibility of CV screens (Chrome, Firefox, Edge).
    Owner: Bonny

    Target Browsers:
    1. Google Chrome (Chromium / Blink)
    2. Microsoft Edge (Chromium / EdgeHTML compatibility)
    3. Mozilla Firefox (Gecko)

    Scope across each browser:
    - CV Studio: /student/cv
    - CV Results: /student/cv/results
    - CV-Job Match: /student/cv/match
    - Tab switching between Review and Match
    - Score rendering and DOM consistency parity
    """

    def test_tc_uit01_t9_01_chrome_cv_screens(self, driver):
        """
        TC-UIT-01-T9-01: Verify CV screens render and navigate cleanly in Google Chrome (Headless).
        """
        email = "bonny_xbrowser_chrome@careerflow.test"
        login_student_browser(driver, email, name="Bonny Chrome Tester")
        prepare_cross_browser_candidate(email)

        wait = WebDriverWait(driver, 12)

        # 1. Test CV Studio
        driver.get(f"{FRONTEND_URL}/student/cv")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-dropzone']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))

        # 2. Test CV Results
        driver.get(f"{FRONTEND_URL}/student/cv/results")
        score_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-overall-score']")))
        assert score_el.text.strip().isdigit()

        # 3. Test Tab Navigation to Match
        tab_match = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-job-match']")))
        tab_match.click()
        wait.until(EC.url_contains("/student/cv/match"))

        # 4. Test Match Screen
        match_score = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))
        assert match_score.text.strip().isdigit()

    def test_tc_uit01_t9_02_edge_cv_screens(self, edge_driver):
        """
        TC-UIT-01-T9-02: Verify CV screens render and navigate cleanly in Microsoft Edge (Headless).
        """
        email = "bonny_xbrowser_edge@careerflow.test"
        login_student_browser(edge_driver, email, name="Bonny Edge Tester")
        prepare_cross_browser_candidate(email)

        wait = WebDriverWait(edge_driver, 12)

        # 1. Test CV Studio
        edge_driver.get(f"{FRONTEND_URL}/student/cv")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-dropzone']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))

        # 2. Test CV Results
        edge_driver.get(f"{FRONTEND_URL}/student/cv/results")
        score_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-overall-score']")))
        assert score_el.text.strip().isdigit()
        tier_badge = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='score-tier-badge']")))
        assert len(tier_badge.text.strip()) > 0

        # 3. Test Tab Navigation to Match
        tab_match = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-job-match']")))
        tab_match.click()
        wait.until(EC.url_contains("/student/cv/match"))

        # 4. Test Match Screen
        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        assert hero_card.is_displayed()
        match_score = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))
        assert match_score.text.strip().isdigit()

    def test_tc_uit01_t9_03_firefox_cv_screens(self, firefox_driver):
        """
        TC-UIT-01-T9-03: Verify CV screens render and navigate cleanly in Mozilla Firefox (Headless Gecko).
        """
        email = "bonny_xbrowser_firefox@careerflow.test"
        login_student_browser(firefox_driver, email, name="Bonny Firefox Tester")
        prepare_cross_browser_candidate(email)

        wait = WebDriverWait(firefox_driver, 12)

        # 1. Test CV Studio
        firefox_driver.get(f"{FRONTEND_URL}/student/cv")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-dropzone']")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-current-cv-name']")))

        # 2. Test CV Results
        firefox_driver.get(f"{FRONTEND_URL}/student/cv/results")
        score_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='cv-overall-score']")))
        assert score_el.text.strip().isdigit()
        breakdown = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='signal-breakdown']")))
        assert breakdown.is_displayed()

        # 3. Test Tab Navigation to Match
        tab_match = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='tab-job-match']")))
        tab_match.click()
        wait.until(EC.url_contains("/student/cv/match"))

        # 4. Test Match Screen
        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        assert hero_card.is_displayed()
        match_score = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))
        assert match_score.text.strip().isdigit()

    def test_tc_uit01_t9_04_cross_browser_score_parity(self, driver, edge_driver, firefox_driver):
        """
        TC-UIT-01-T9-04: Cross-browser parity check.
        Verify that Chrome, Edge, and Firefox display identical overall scores and match scores for the same candidate data.
        """
        email = "bonny_xbrowser_parity@careerflow.test"
        prepare_cross_browser_candidate(email)

        # Chrome read
        login_student_browser(driver, email, name="Bonny Parity")
        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait_c = WebDriverWait(driver, 10)
        c_score = int(wait_c.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']"))).text.strip())

        # Edge read
        login_student_browser(edge_driver, email, name="Bonny Parity")
        edge_driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait_e = WebDriverWait(edge_driver, 10)
        e_score = int(wait_e.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']"))).text.strip())

        # Firefox read
        login_student_browser(firefox_driver, email, name="Bonny Parity")
        firefox_driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait_f = WebDriverWait(firefox_driver, 10)
        f_score = int(wait_f.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']"))).text.strip())

        assert c_score == e_score == f_score, f"Parity mismatch! Chrome: {c_score}, Edge: {e_score}, Firefox: {f_score}"
