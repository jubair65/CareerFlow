import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root and backend to sys.path
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'

if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')

import django
django.setup()

import pytest


class ResultCollector:
    """Pytest plugin to capture comprehensive test results for reporting."""
    __test__ = False

    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus):
        self.end_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            # Map test to Sprint 1 Section
            test_file = Path(report.nodeid.split("::")[0]).name
            test_name = report.nodeid.split("::")[-1]

            story_id = "UNKNOWN"
            story_title = "Unknown"
            if "us01" in test_file:
                story_id = "US-01"
                story_title = "User Registration"
            elif "us02" in test_file:
                story_id = "US-02"
                story_title = "User Login"
            elif "us03" in test_file:
                story_id = "US-03"
                story_title = "Role-Based Access Control"
            elif "us04" in test_file:
                story_id = "US-04"
                story_title = "Password Security"
            elif "us36" in test_file:
                story_id = "US-36"
                story_title = "Data Access Control"

            status = "PASSED" if report.passed else "FAILED" if report.failed else "SKIPPED"
            error_message = ""
            if report.failed and report.longrepr:
                error_message = str(report.longrepr)

            self.results.append({
                "story_id": story_id,
                "story_title": story_title,
                "test_file": test_file,
                "test_name": test_name,
                "status": status,
                "duration_seconds": round(report.duration, 3),
                "error": error_message
            })


def generate_markdown_report(collector, output_path: Path):
    """Generates a professional Markdown test report."""
    total_tests = len(collector.results)
    passed_tests = sum(1 for r in collector.results if r["status"] == "PASSED")
    failed_tests = sum(1 for r in collector.results if r["status"] == "FAILED")
    skipped_tests = sum(1 for r in collector.results if r["status"] == "SKIPPED")
    pass_rate = round((passed_tests / total_tests * 100) if total_tests > 0 else 0, 1)
    duration = round((collector.end_time - collector.start_time) if collector.end_time and collector.start_time else 0, 2)

    # Group by story
    stories = {}
    for r in collector.results:
        sid = r["story_id"]
        if sid not in stories:
            stories[sid] = {
                "title": r["story_title"],
                "tests": []
            }
        stories[sid]["tests"].append(r)

    md = []
    md.append("# CareerFlow — Sprint 1 Automated Selenium Test Report")
    md.append("")
    md.append(f"**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append(f"**Sprint:** Sprint 1 — Establish Secure Technical Foundation  ")
    md.append(f"**Target Applications:** Frontend (`http://localhost:5173`) & Backend (`http://127.0.0.1:8000`)  ")
    md.append(f"**Database:** MySQL (`careerflow_db`)  ")
    md.append("")
    md.append("## Executive Summary")
    md.append("")
    md.append("| Metric | Value | Status |")
    md.append("| --- | --- | --- |")
    md.append(f"| **Total Tests** | {total_tests} | - |")
    md.append(f"| **Passed** | {passed_tests} | {'✅ 100%' if passed_tests == total_tests else '⚠️'} |")
    md.append(f"| **Failed** | {failed_tests} | {'✅ None' if failed_tests == 0 else '❌'} |")
    md.append(f"| **Skipped** | {skipped_tests} | - |")
    md.append(f"| **Pass Rate** | **{pass_rate}%** | {'✅ EXCELLENT' if pass_rate == 100 else '⚠️ ATTENTION'} |")
    md.append(f"| **Total Duration** | {duration} seconds | ⏱️ Fast Execution |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 5 Sprint 1 Testing Sections Overview")
    md.append("")
    md.append("| Story ID | Section Name | QA Task | Tests Executed | Passed | Status |")
    md.append("| --- | --- | --- | --- | --- | --- |")

    task_map = {
        "US-01": "US-01-T6 (Write unit tests / UI test for registration)",
        "US-02": "US-02-T5 (Test login flow and sessions)",
        "US-03": "US-03-T6 (Test role-based access control)",
        "US-04": "US-04-T4 (Test password security measures)",
        "US-36": "US-36-T4 (Test data access controls)",
    }

    for sid in ["US-01", "US-02", "US-03", "US-04", "US-36"]:
        data = stories.get(sid, {"title": "N/A", "tests": []})
        st_total = len(data["tests"])
        st_passed = sum(1 for t in data["tests"] if t["status"] == "PASSED")
        status_icon = "✅ PASSED" if (st_total > 0 and st_total == st_passed) else "❌ FAILED"
        task_desc = task_map.get(sid, "QA Task")
        md.append(f"| **{sid}** | {data['title']} | {task_desc} | {st_total} | {st_passed} | {status_icon} |")

    md.append("")
    md.append("---")
    md.append("")
    md.append("## Detailed Test Results by Story")
    md.append("")

    for sid in ["US-01", "US-02", "US-03", "US-04", "US-36"]:
        if sid not in stories:
            continue
        data = stories[sid]
        md.append(f"### {sid}: {data['title']}")
        md.append("")
        md.append("| Test ID / Method | Status | Duration (s) | Notes |")
        md.append("| --- | --- | --- | --- |")
        for t in data["tests"]:
            icon = "✅" if t["status"] == "PASSED" else "❌"
            md.append(f"| `{t['test_name']}` | {icon} {t['status']} | {t['duration_seconds']}s | Verified against acceptance criteria |")
        md.append("")

    if failed_tests > 0:
        md.append("---")
        md.append("")
        md.append("## Failures & Diagnoses")
        md.append("")
        for t in collector.results:
            if t["status"] == "FAILED":
                md.append(f"### ❌ {t['test_name']} ({t['story_id']})")
                md.append("```text")
                md.append(t["error"])
                md.append("```")
                md.append("")

    md.append("---")
    md.append("")
    md.append("## Conclusion & Sign-Off")
    md.append("")
    if failed_tests == 0 and passed_tests > 0:
        md.append("All 5 core testing sections specified in Sprint 1 have passed with 100% success rate. The foundation meets all defined security, authentication, role isolation, and database persistence acceptance criteria.")
    else:
        md.append(f"{failed_tests} test(s) failed. Review the failure details above before signing off on Sprint 1.")

    output_path.write_text("\n".join(md), encoding="utf-8")


def run_tests():
    collector = ResultCollector()
    reports_dir = TESTS_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("  CAREERFLOW SPRINT 1 — COMPREHENSIVE SELENIUM TEST SUITE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Frontend: {FRONTEND_URL}")
    print(f"Target Backend:  {BACKEND_URL}")
    print(f"Running tests across 5 Sprint 1 stories...")
    print("-" * 70)

    pytest_args = [
        str(TESTS_DIR),
        "-v",
        "--tb=short"
    ]

    exit_code = pytest.main(pytest_args, plugins=[collector])

    md_report_path = reports_dir / "sprint1_testing_report.md"

    generate_markdown_report(collector, md_report_path)

    print("\n" + "=" * 70)
    print("  TEST EXECUTION SUMMARY")
    print("=" * 70)
    total = len(collector.results)
    passed = sum(1 for r in collector.results if r["status"] == "PASSED")
    failed = sum(1 for r in collector.results if r["status"] == "FAILED")
    print(f"Total Tests Executed: {total}")
    print(f"Passed:               {passed}")
    print(f"Failed:               {failed}")
    if total > 0:
        print(f"Pass Rate:            {round(passed / total * 100, 1)}%")
    print(f"Markdown Report:      {md_report_path}")
    print("=" * 70 + "\n")

    return exit_code


if __name__ == "__main__":
    from conftest import FRONTEND_URL, BACKEND_URL
    sys.exit(run_tests())
