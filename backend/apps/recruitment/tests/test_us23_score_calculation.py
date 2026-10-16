import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV, ParsedCV, JobRequirement, CVJobMatch
from apps.presentation.models import PresentationVideo, PresentationScore
from apps.recruitment.services.scoring_service import (
    resolve_room_weights,
    compute_weighted_score,
    calculate_application_score,
    calculate_room_applicant_scores,
    DEFAULT_CV_WEIGHT,
    DEFAULT_VIDEO_WEIGHT,
)


class US23FinalScoreCalculationTests(APITestCase):
    """
    US-23: Final Applicant Score Calculation Comprehensive Test Suite (US-23-T7).
    Covers:
    - AC#1: Final score calculated from CV and Video scores using room weights.
    - AC#2: Default 50/50 weighting applied if room weights are missing/null.
    - AC#3: Missing CV or Video scores handled gracefully with is_partial_score=True.
    - AC#4: Final scores recalculated automatically on weight changes or pipeline updates.
    - AC#5: Final score stored in database, indexed, and timestamped.
    - AC#6: Deterministic, accurate, and mathematically exact calculations.
    """

    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_owner_{self.uid}",
            email=f"hr_owner_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Fatima Al-Sayed"
        )

        # 2. Other HR User (Unauthorized Non-Owner)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_{self.uid}",
            email=f"other_hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Marcus Vance"
        )

        # 3. Student / Candidate Users
        self.candidate_alice = User.objects.create_user(
            username=f"alice_{self.uid}",
            email=f"alice_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Alice Candidate"
        )
        self.candidate_bob = User.objects.create_user(
            username=f"bob_{self.uid}",
            email=f"bob_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Bob Candidate"
        )
        self.candidate_charlie = User.objects.create_user(
            username=f"charlie_{self.uid}",
            email=f"charlie_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Charlie Candidate"
        )
        self.candidate_david = User.objects.create_user(
            username=f"david_{self.uid}",
            email=f"david_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="David Candidate"
        )

        # 4. Recruitment Room with 60% CV / 40% Video custom weights
        self.room = RecruitmentRoom.objects.create(
            title="Senior Full Stack Engineer",
            company_name="Innovatech Labs",
            department="Cloud Engineering",
            role_category="Engineering",
            experience_level=RecruitmentRoom.ExperienceLevel.SENIOR,
            status=RecruitmentRoom.Status.ACTIVE,
            requirements_text="Proficiency in React, Django, Python, Docker",
            skills_required=["React", "Django", "Python", "Docker"],
            cv_weight=60,
            video_weight=40,
            created_by=self.hr_owner
        )

        # 5. JobRequirement linked to Room
        self.job_req = JobRequirement.objects.create(
            title=self.room.title,
            company=self.room.company_name,
            role_type="Engineering",
            description=self.room.requirements_text,
            required_skills=self.room.skills_required,
            threshold_score=70,
            created_by=self.hr_owner
        )

        # 6. Alice has both CV (score 85) and Video (score 90)
        self.alice_cv = CandidateCV.objects.create(
            user=self.candidate_alice,
            file="students/alice/resume.pdf",
            original_filename="Alice_Resume.pdf",
            file_size=102400,
            file_type="pdf"
        )
        self.alice_cv_match = CVJobMatch.objects.create(
            cv=self.alice_cv,
            job=self.job_req,
            job_title=self.room.title,
            company=self.room.company_name,
            match_score=85,
            keyword_coverage=80
        )
        self.alice_video = PresentationVideo.objects.create(
            user=self.candidate_alice,
            file="students/alice/video.mp4",
            original_filename="Alice_Pitch.mp4",
            raw_file_size=2048000,
            file_type="mp4",
            status="COMPLETED"
        )
        self.alice_ps = PresentationScore.objects.create(
            video=self.alice_video,
            overall_score=90,
            speech_score=88,
            behavioral_score=92
        )
        self.app_alice = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_alice,
            cv=self.alice_cv,
            video=self.alice_video,
            status=CandidateApplication.Status.COMPLETED
        )

        # 7. Bob has CV only (score 78), video is missing
        self.bob_cv = CandidateCV.objects.create(
            user=self.candidate_bob,
            file="students/bob/resume.pdf",
            original_filename="Bob_Resume.pdf",
            file_size=102400,
            file_type="pdf"
        )
        self.bob_cv_match = CVJobMatch.objects.create(
            cv=self.bob_cv,
            job=self.job_req,
            job_title=self.room.title,
            company=self.room.company_name,
            match_score=78,
            keyword_coverage=70
        )
        self.app_bob = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_bob,
            cv=self.bob_cv,
            video=None,
            status=CandidateApplication.Status.COMPLETED
        )

        # 8. Charlie has Video only (score 82), CV is missing
        self.charlie_video = PresentationVideo.objects.create(
            user=self.candidate_charlie,
            file="students/charlie/video.mp4",
            original_filename="Charlie_Pitch.mp4",
            raw_file_size=2048000,
            file_type="mp4",
            status="COMPLETED"
        )
        self.charlie_ps = PresentationScore.objects.create(
            video=self.charlie_video,
            overall_score=82,
            speech_score=80,
            behavioral_score=84
        )
        self.app_charlie = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_charlie,
            cv=None,
            video=self.charlie_video,
            status=CandidateApplication.Status.COMPLETED
        )

        # 9. David has neither CV nor Video
        self.app_david = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate_david,
            cv=None,
            video=None,
            status=CandidateApplication.Status.PENDING
        )

    # =========================================================================
    # Task US-23-T1: Mathematical Formula & Weight Validation
    # =========================================================================

    def test_default_weighting_fallback(self):
        """Room without explicit weights defaults to 50% CV / 50% Video (AC#2)."""
        cv_w, vid_w = resolve_room_weights(None)
        self.assertEqual(cv_w, DEFAULT_CV_WEIGHT)
        self.assertEqual(vid_w, DEFAULT_VIDEO_WEIGHT)

        # Dummy room with None weights
        class MockRoom:
            cv_weight = None
            video_weight = None
        cv_w2, vid_w2 = resolve_room_weights(MockRoom())
        self.assertEqual(cv_w2, 50)
        self.assertEqual(vid_w2, 50)

    def test_invalid_weight_sum_falls_back_to_50_50(self):
        """Weights that do not sum to 100% fallback to 50/50."""
        class MockRoom:
            id = 999
            cv_weight = 70
            video_weight = 40  # Sums to 110 != 100
        cv_w, vid_w = resolve_room_weights(MockRoom())
        self.assertEqual(cv_w, 50)
        self.assertEqual(vid_w, 50)

    def test_pure_formula_precision(self):
        """Formula produces deterministic, accurate results rounded to 1 decimal place (AC#6)."""
        # (60 * 85.0 + 40 * 90.0) / 100 = (5100 + 3600) / 100 = 87.0
        score, is_partial = compute_weighted_score(85.0, 90.0, 60, 40)
        self.assertEqual(score, 87.0)
        self.assertFalse(is_partial)

        # Precision test: 70% CV (85.3) + 30% Video (72.8)
        # = (59.71 + 21.84) = 81.55 -> rounded to 81.6
        score, is_partial = compute_weighted_score(85.3, 72.8, 70, 30)
        self.assertEqual(score, 81.6)
        self.assertFalse(is_partial)

    # =========================================================================
    # Task US-23-T2 & US-23-T3: Service Integration (CV + Video)
    # =========================================================================

    def test_calculate_application_score_both_components(self):
        """Calculates correct composite score when both CV and Video are present (AC#1)."""
        result = calculate_application_score(self.app_alice, persist=True)

        self.assertEqual(result["cv_score"], 85.0)
        self.assertEqual(result["video_score"], 90.0)
        # 60% of 85 = 51.0, 40% of 90 = 36.0 -> 87.0
        self.assertEqual(result["final_score"], 87.0)
        self.assertFalse(result["is_partial_score"])

        # Check DB persistence (AC#5)
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 87.0)
        self.assertEqual(self.app_alice.cv_score, 85.0)
        self.assertEqual(self.app_alice.video_score, 90.0)
        self.assertFalse(self.app_alice.is_partial_score)
        self.assertIsNotNone(self.app_alice.score_calculated_at)

    # =========================================================================
    # Task US-23-T4: Missing & Incomplete Component Handling
    # =========================================================================

    def test_missing_video_handles_gracefully(self):
        """Missing video proportionally re-scales to CV match score with is_partial=True (AC#3)."""
        result = calculate_application_score(self.app_bob, persist=True)

        self.assertEqual(result["cv_score"], 78.0)
        self.assertIsNone(result["video_score"])
        self.assertEqual(result["final_score"], 78.0)
        self.assertTrue(result["is_partial_score"])

        self.app_bob.refresh_from_db()
        self.assertEqual(self.app_bob.final_score, 78.0)
        self.assertTrue(self.app_bob.is_partial_score)

    def test_missing_cv_handles_gracefully(self):
        """Missing CV proportionally re-scales to video presentation score with is_partial=True (AC#3)."""
        result = calculate_application_score(self.app_charlie, persist=True)

        self.assertIsNone(result["cv_score"])
        self.assertEqual(result["video_score"], 82.0)
        self.assertEqual(result["final_score"], 82.0)
        self.assertTrue(result["is_partial_score"])

        self.app_charlie.refresh_from_db()
        self.assertEqual(self.app_charlie.final_score, 82.0)
        self.assertTrue(self.app_charlie.is_partial_score)

    def test_both_missing_produces_none_final_score(self):
        """Application with neither CV nor Video yields None final_score without crashing (AC#3)."""
        result = calculate_application_score(self.app_david, persist=True)

        self.assertIsNone(result["cv_score"])
        self.assertIsNone(result["video_score"])
        self.assertIsNone(result["final_score"])
        self.assertFalse(result["is_partial_score"])

        self.app_david.refresh_from_db()
        self.assertIsNone(self.app_david.final_score)

    # =========================================================================
    # Task US-23-T4: Boundary & Extreme Weighting Scenarios
    # =========================================================================

    def test_extreme_weight_100_percent_cv(self):
        """100% CV weight ignores video score entirely."""
        score, is_partial = compute_weighted_score(88.0, 40.0, 100, 0)
        self.assertEqual(score, 88.0)
        self.assertFalse(is_partial)

    def test_extreme_weight_100_percent_video(self):
        """100% Video weight ignores CV score entirely."""
        score, is_partial = compute_weighted_score(40.0, 92.0, 0, 100)
        self.assertEqual(score, 92.0)
        self.assertFalse(is_partial)

    def test_zero_scores_boundary(self):
        """Zero scores calculate to 0.0 without division or null errors."""
        score, is_partial = compute_weighted_score(0.0, 0.0, 50, 50)
        self.assertEqual(score, 0.0)
        self.assertFalse(is_partial)

    def test_perfect_scores_boundary(self):
        """100% scores on both components yield 100.0."""
        score, is_partial = compute_weighted_score(100.0, 100.0, 60, 40)
        self.assertEqual(score, 100.0)
        self.assertFalse(is_partial)

    # =========================================================================
    # Task US-23-T5: Automated Recalculation on Weight Changes & Signal Triggers
    # =========================================================================

    def test_room_weight_update_triggers_recalculation(self):
        """Modifying room weights automatically recalculates application scores (AC#4)."""
        # Calculate initial score: 60/40 split -> 87.0
        calculate_application_score(self.app_alice, persist=True)
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 87.0)

        # Change room weights to 20% CV / 80% Video
        # New expected: (20 * 85 + 80 * 90) / 100 = (1700 + 7200) / 100 = 89.0
        self.room.cv_weight = 20
        self.room.video_weight = 80
        self.room.save(update_fields=['cv_weight', 'video_weight'])

        # Verify Alice's application was automatically recalculated by signal
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 89.0)

    def test_presentation_score_signal_triggers_recalculation(self):
        """Updating a PresentationScore triggers application score recalculation (AC#4)."""
        calculate_application_score(self.app_alice, persist=True)
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 87.0)

        # Alice re-takes pitch video and achieves overall_score of 95
        # (60 * 85 + 40 * 95) / 100 = (5100 + 3800) / 100 = 89.0
        self.alice_ps.overall_score = 95
        self.alice_ps.save()

        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.video_score, 95.0)
        self.assertEqual(self.app_alice.final_score, 89.0)

    def test_cv_match_signal_triggers_recalculation(self):
        """Updating CVJobMatch triggers application score recalculation (AC#4)."""
        calculate_application_score(self.app_alice, persist=True)
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 87.0)

        # Alice updates CV and match score increases to 95
        # (60 * 95 + 40 * 90) / 100 = (5700 + 3600) / 100 = 93.0
        self.alice_cv_match.match_score = 95
        self.alice_cv_match.save()

        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.cv_score, 95.0)
        self.assertEqual(self.app_alice.final_score, 93.0)

    # =========================================================================
    # Task US-23-T5: Batch Recalculation API Endpoint
    # =========================================================================

    def test_calculate_scores_api_as_room_owner_success(self):
        """Room owner can invoke POST /api/recruitment/rooms/{id}/calculate-scores/ (US-23-T5)."""
        self.client.force_authenticate(user=self.hr_owner)
        url = f"/api/recruitment/rooms/{self.room.id}/calculate-scores/"

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["weights_used"]["cv_weight"], 60)
        self.assertEqual(data["weights_used"]["video_weight"], 40)
        self.assertEqual(data["processed_count"], 4)
        # Alice (87), Bob (78), Charlie (82) are updated; David is None
        self.assertEqual(data["updated_count"], 3)

        # Check DB states
        self.app_alice.refresh_from_db()
        self.assertEqual(self.app_alice.final_score, 87.0)

        self.app_bob.refresh_from_db()
        self.assertEqual(self.app_bob.final_score, 78.0)

        self.app_charlie.refresh_from_db()
        self.assertEqual(self.app_charlie.final_score, 82.0)

    def test_calculate_scores_api_unauthorized_for_non_owner(self):
        """Non-owner HR Manager cannot trigger score recalculation for another's room."""
        self.client.force_authenticate(user=self.other_hr)
        url = f"/api/recruitment/rooms/{self.room.id}/calculate-scores/"

        response = self.client.post(url)
        # 404 Not Found is returned because get_queryset restricts to created_by=user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_calculate_scores_api_unauthenticated_fails(self):
        """Unauthenticated call to calculate-scores endpoint is rejected with 401."""
        url = f"/api/recruitment/rooms/{self.room.id}/calculate-scores/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
