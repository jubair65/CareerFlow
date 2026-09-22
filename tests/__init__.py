import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for p in [str(PROJECT_ROOT), str(TESTS_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)
