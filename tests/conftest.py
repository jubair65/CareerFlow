import os
import sys
import shutil
from pathlib import Path
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Initialize Django environment
BACKEND_DIR = Path(__file__).resolve().parent.parent / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
import django
django.setup()

from apps.authentication.models import User
from apps.core.models import DataAccessLog
from django.conf import settings

FRONTEND_URL = "http://localhost:5173"
BACKEND_URL = "http://127.0.0.1:8000"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_chrome_options():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--log-level=3')
    return options


@pytest.fixture(scope="function")
def driver(request):
    """Provides a clean headless Chrome WebDriver instance for each test."""
    options = get_chrome_options()
    driver_instance = webdriver.Chrome(options=options)
    driver_instance.implicitly_wait(10)

    yield driver_instance

    driver_instance.quit()


@pytest.fixture(autouse=True)
def clean_test_data():
    """Clean up test users created during test runs."""
    yield
    # Clean up test accounts ending in @careerflow.test or containing test_
    User.objects.filter(email__icontains="test_").delete()
    User.objects.filter(email__endswith="@careerflow.test").delete()


def create_user_in_db(email, password, role=User.Role.STUDENT, full_name="Test User"):
    """Helper to create user directly in MySQL database with proper password hashing."""
    User.objects.filter(email__iexact=email).delete()
    username = email.split('@')[0]
    user = User(
        email=email.lower(),
        username=username,
        role=role,
        full_name=full_name,
        is_active=True
    )
    user.set_password(password)
    user.save()
    return user


def setup_test_media_files():
    """Ensure media directory exists with sample test student CV files."""
    media_root = Path(settings.MEDIA_ROOT).resolve()
    media_root.mkdir(parents=True, exist_ok=True)
    return media_root
