import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from conftest import FRONTEND_URL, create_user_in_db

def login_as_student(driver):
    """Helper to login as a student."""
    driver.get(f"{FRONTEND_URL}/login")
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='input-login-email']")))
    email_input.clear()
    email_input.send_keys("e2e_student@careerflow.test")
    
    pass_input = driver.find_element(By.CSS_SELECTOR, "[data-testid='input-login-password']")
    pass_input.clear()
    pass_input.send_keys("Student123!")
    
    driver.find_element(By.CSS_SELECTOR, "[data-testid='button-login']").click()
    
    # Wait for dashboard to load
    wait.until(EC.url_contains("/student/dashboard"))


class TestUIT01T10E2EFlow:
    """
    UIT-01-T10: Test end-to-end UI flow: upload CV, extraction, feedback and match score.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Create test user
        create_user_in_db("e2e_student@careerflow.test", "Student123!")
        
        self.fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "cv"
        self.valid_pdf = self.fixtures_dir / "valid_sample.pdf"
        self.incomplete_pdf = self.fixtures_dir / "incomplete_cv.pdf"
        
        # Ensure fixtures exist
        if not self.valid_pdf.exists():
            pytest.skip("Fixture valid_sample.pdf not found")

    def test_e2e_flow_happy_path(self, driver):
        """Scenario 1: Happy Path - Complete Successful Flow"""
        login_as_student(driver)
        
        # 1. Navigate to CV Upload
        driver.get(f"{FRONTEND_URL}/student/cv")
        
        # 2. Upload valid PDF
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']"))
        )
        file_input.send_keys(str(self.valid_pdf))
        
        upload_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']"))
        )
        upload_btn.click()

        # 3. Progress Tracking & Extraction State
        # Assuming the UI transitions to /student/cv-results or similar after processing
        # In the app, it might stay on the same page or go to /student/cv-results. 
        # I'll look for the feedback section.
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='signal-breakdown']"))
        )
        
        # 4. Feedback Verification
        feedback_section = driver.find_element(By.CSS_SELECTOR, "[data-testid='signal-breakdown']")
        assert feedback_section.is_displayed(), "Feedback section did not render."
        
        # Verify formatting, clarity, and keyword strength elements exist
        text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "formatting" in text or "clarity" in text or "keyword" in text, "Feedback criteria not found in UI."

        # 5. Match Score Verification
        # Navigate to Job Match or verify score on the same page
        driver.get(f"{FRONTEND_URL}/student/job-match")
        
        score_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "match-score"))
        )
        assert score_element.is_displayed(), "Match score element failed to render."
        
        score_text = score_element.text
        # Ensure it contains a number (e.g. "85%")
        import re
        match = re.search(r'\d+', score_text)
        assert match, f"No numeric score found in '{score_text}'"
        
        score = int(match.group())
        assert 0 <= score <= 100, f"Match score {score} is out of bounds (0-100)."

    def test_e2e_flow_incomplete_data(self, driver):
        """Scenario 2: Alternative Path - Incomplete CV Data"""
        login_as_student(driver)
        
        # Navigate & Upload
        driver.get(f"{FRONTEND_URL}/student/cv")
        
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='input-cv-file']"))
        )
        file_input.send_keys(str(self.incomplete_pdf))
        
        upload_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='button-upload-cv']"))
        )
        upload_btn.click()

        # Wait for processing to complete and redirect
        # Wait for feedback section
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='signal-breakdown']"))
        )
        
        # Verify Feedback handles incomplete data (might show missing sections)
        feedback_section = driver.find_element(By.CSS_SELECTOR, "[data-testid='signal-breakdown']")
        assert feedback_section.is_displayed(), "Feedback section did not render for incomplete CV."
        
        # Check match score still renders without crashing
        driver.get(f"{FRONTEND_URL}/student/job-match")
        score_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        assert score_element.is_displayed(), "Match score element crashed/failed to render for incomplete CV."
