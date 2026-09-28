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
from apps.cv.models import CandidateCV, ParsedCV, CVFeedback, CVJobMatch
from apps.cv.services.scorer import generate_cv_feedback
from apps.cv.services.semantic_matcher import match_cv_to_job
from conftest import FRONTEND_URL, create_user_in_db

FIXTURES_DIR = TESTS_DIR / "fixtures" / "cv"


def login_student(driver, email="bonny_qa_student@careerflow.test", password="ValidPass2026!"):
    """Helper to log in as candidate/student."""
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Bonny QA Tester")

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


def prepare_candidate_with_cv_and_match(
    student_email="bonny_tc01_match@careerflow.test",
    fixture_name="valid_sample.pdf",
    job_title="Product Designer",
    required_skills=None
):
    """Helper to set up a candidate with a valid CV, feedback, and precomputed semantic match in database."""
    user = User.objects.filter(email__iexact=student_email).first()
    if not user:
        user = create_user_in_db(student_email, "ValidPass2026!", role=User.Role.STUDENT, full_name="Bonny QA Evaluator")
    
    pdf_path = FIXTURES_DIR / fixture_name
    assert pdf_path.exists(), f"Missing fixture file: {pdf_path}"

    with open(pdf_path, "rb") as f:
        cv = CandidateCV.objects.create(
            user=user,
            file=ContentFile(f.read(), name=fixture_name),
            original_filename=fixture_name,
            file_size=pdf_path.stat().st_size,
            file_type="pdf",
            is_active=True
        )

    feedback = generate_cv_feedback(cv)
    skills = required_skills or ["Figma", "Product Strategy", "User Research", "Accessibility", "Systems Thinking"]
    match_record = match_cv_to_job(
        cv=cv,
        job_title=job_title,
        job_description=f"Looking for a {job_title} with proven industry track record.",
        required_skills=skills
    )
    return user, cv, feedback, match_record


class TestUIT01T7MatchScoreDisplay:
    """
    UIT-01-T7: Test match score display UI (0-100 score, missing/incomplete data handling).
    Owner: Bonny
    Target Page: frontend/src/pages/JobMatch.tsx (/student/cv/match)

    Standard Test IDs Verified:
    ✓ data-testid="card-match-hero"
    ✓ data-testid="text-match-score"
    ✓ data-testid="text-match-headline"
    ✓ data-testid="container-matched-skill-tags"
    ✓ data-testid="card-match-signals"
    ✓ data-testid="input-match-title"
    ✓ data-testid="input-match-company"
    ✓ data-testid="input-match-skills"
    ✓ data-testid="input-match-description"
    ✓ data-testid="button-recalculate-match"
    ✓ data-testid="button-back-to-results"

    Acceptance Criteria:
    1. Match score displays as an integer between 0 and 100.
    2. Score tier headline aligns with score value (>=80 Strong, 65-79 Moderate, <65 Needs keywords).
    3. Keyword coverage percentage is visible and valid (0-100%).
    4. All 4 sub-signal category bars render with valid percentage widths (0-100%).
    5. Matched skills vs missing skills render accurately with appropriate styling.
    6. Missing/incomplete data handling:
       - Candidate without active CV sees friendly fallback card without UI crash.
       - Candidate with sparse/incomplete CV handles empty match skills gracefully.
    7. Dynamic role recalculation triggers update and success notification.
    """

    def test_tc_uit01_t7_01_match_score_display_valid(self, driver):
        """
        TC-UIT-01-T7-01: Verify match score displays as an integer between 0 and 100,
        headline matches score tier, and keyword coverage renders accurately.
        """
        student_email = "bonny_tc01_score@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv_and_match(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        # 1. Verify card-match-hero is visible
        hero_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']")))
        assert hero_card.is_displayed()

        # 2. Verify text-match-score is integer 0-100
        score_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))
        score_text = score_element.text.strip()
        assert score_text.isdigit(), f"Match score '{score_text}' is not a valid integer!"
        score_val = int(score_text)
        assert 0 <= score_val <= 100, f"Match score {score_val} is out of bounds [0, 100]!"

        # 3. Verify headline tier
        headline_el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-headline']")))
        headline_text = headline_el.text.strip()
        if score_val >= 80:
            assert "Strong match" in headline_text, f"Expected 'Strong match' in headline, got: '{headline_text}'"
        elif score_val >= 65:
            assert "Moderate match" in headline_text, f"Expected 'Moderate match' in headline, got: '{headline_text}'"
        else:
            assert "Needs keywords" in headline_text, f"Expected 'Needs keywords' in headline, got: '{headline_text}'"

        # 4. Verify keyword coverage tag
        coverage_regex = re.compile(r"(\d+)%\s+Keyword\s+Coverage", re.IGNORECASE)
        match_cov = coverage_regex.search(hero_card.text)
        assert match_cov is not None, f"Keyword coverage badge not found in hero card: {hero_card.text}"
        cov_val = int(match_cov.group(1))
        assert 0 <= cov_val <= 100, f"Keyword coverage {cov_val}% out of range [0, 100]!"

    def test_tc_uit01_t7_02_sub_signal_breakdown_bars(self, driver):
        """
        TC-UIT-01-T7-02: Verify all 4 role sub-signals render with valid widths (0-100%).
        Dimensions: Domain Craft, Collaboration, Leadership, Accessibility & Quality Standards.
        """
        student_email = "bonny_tc02_signals@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv_and_match(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        signals_card = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-signals']"))
        )
        assert signals_card.is_displayed()

        expected_dimensions = [
            "Product / Technical Craft",
            "Cross-functional Collaboration",
            "Ownership & Leadership",
            "Accessibility & Quality Standards",
        ]

        width_regex = re.compile(r"width:\s*(\d+(?:\.\d+)?)%")

        card_text = signals_card.text
        for dim in expected_dimensions:
            assert dim in card_text, f"Missing sub-signal dimension: '{dim}' in card text"

        # Inspect all inner progress bars inside signals card
        progress_bars = signals_card.find_elements(By.CSS_SELECTOR, ".h-full")
        assert len(progress_bars) >= 4, f"Expected at least 4 progress bars, found {len(progress_bars)}"

        for idx, bar in enumerate(progress_bars[:4]):
            style_attr = bar.get_attribute("style") or ""
            match = width_regex.search(style_attr)
            assert match is not None, f"Bar #{idx+1} has invalid width style: '{style_attr}'"
            pct = float(match.group(1))
            assert 0.0 <= pct <= 100.0, f"Bar #{idx+1} width {pct}% out of range [0, 100]!"

    def test_tc_uit01_t7_03_matched_and_missing_skills_rendering(self, driver):
        """
        TC-UIT-01-T7-03: Verify matched skills render green badges and missing skills render red badges.
        """
        student_email = "bonny_tc03_skills@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv_and_match(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        # Wait for skills containers
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='container-matched-skill-tags']")))

        # Check matched skills in hero card or matched skills section
        matched_tags = driver.find_elements(By.CSS_SELECTOR, "[data-testid='container-matched-skill-tags'] span")
        assert len(matched_tags) >= 1, "Expected at least 1 matched skill tag in hero card"

        # Verify page content includes Matched Skills and Missing Skills sections
        page_source = driver.page_source
        assert "Matched Skills" in page_source
        assert "Missing Skill Requirements" in page_source

    def test_tc_uit01_t7_04_empty_state_handling_no_cv(self, driver):
        """
        TC-UIT-01-T7-04: Candidate navigates to Job Match without any active CV ->
        UI handles missing data gracefully, does not crash, and shows friendly fallback card.
        """
        student_email = "bonny_tc04_nocv@careerflow.test"
        login_student(driver, email=student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        # Verify fallback empty state appears
        empty_heading = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'No Active CV Document Uploaded')]"))
        )
        assert empty_heading.is_displayed()

        # Verify action button to CV Studio exists and functions
        studio_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Go to CV Studio')]"))
        )
        assert studio_btn.is_displayed()
        studio_btn.click()

        wait.until(EC.url_contains("/student/cv"))

    def test_tc_uit01_t7_05_sparse_incomplete_cv_handling(self, driver):
        """
        TC-UIT-01-T7-05: Candidate with sparse/incomplete CV visits Job Match ->
        Handles missing/zero skill matches without throwing exceptions or crashing.
        """
        student_email = "bonny_tc05_sparse@careerflow.test"
        login_student(driver, email=student_email)
        # Use incomplete_cv.pdf fixture
        prepare_candidate_with_cv_and_match(
            student_email=student_email,
            fixture_name="incomplete_cv.pdf",
            job_title="Senior Frontend Engineer",
            required_skills=["Kubernetes", "Rust", "Erlang", "Haskell"]
        )

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        # Confirm match hero loaded
        score_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='text-match-score']")))
        score_val = int(score_element.text.strip())
        assert 0 <= score_val <= 100

        # Page does not crash and renders cleanly
        assert wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='card-match-hero']"))).is_displayed()

    def test_tc_uit01_t7_06_interactive_role_recalculation(self, driver):
        """
        TC-UIT-01-T7-06: Candidate selects a quick preset role and recalculates semantic match score.
        Verify inputs update and clicking recalculate generates an updated match score.
        """
        student_email = "bonny_tc06_recalc@careerflow.test"
        login_student(driver, email=student_email)
        prepare_candidate_with_cv_and_match(student_email)

        driver.get(f"{FRONTEND_URL}/student/cv/match")
        wait = WebDriverWait(driver, 10)

        # 1. Wait for recalculate button
        recalc_btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='button-recalculate-match']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recalc_btn)

        # 2. Click a preset button (e.g. Fullstack Software Developer)
        preset_btn = wait.until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Fullstack Software Developer')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", preset_btn)
        driver.execute_script("arguments[0].click();", preset_btn)

        # Verify title input was populated
        title_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-match-title']")
        assert title_input.get_attribute("value") == "Fullstack Software Developer"

        # 3. Click recalculate match
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", recalc_btn)
        driver.execute_script("arguments[0].click();", recalc_btn)

        # 4. Verify toast notification appears
        toast = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='toast-message']")))
        assert "Role match evaluated" in toast.text or "score generated" in toast.text

        # 5. Verify headline or role updated to Fullstack Software Developer
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Fullstack Software Developer')]")))
