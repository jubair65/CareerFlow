"""
US-28: Side-by-Side Applicant Comparison Unit & Integration Tests (US-28-T7).
Tests cover:
- Room ownership authorization & access control (AC#6)
- Selection boundary enforcement: min 2, max 4 candidates (AC#5)
- Multi-signal comparison data retrieval: CV, Video, Final scores (AC#2, AC#3)
- Differential calculation & best-in-category highlights (AC#4)
- Graceful degradation for candidates with missing CV/video evaluations (AC#5)
- Rejection of foreign applications belonging to other rooms
"""

import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'careerflow.settings')
django.setup()

from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.recruitment.models import RecruitmentRoom, CandidateApplication
from apps.cv.models import CandidateCV
from apps.presentation.models import PresentationVideo, PresentationScore, SpeechAnalysis, BehavioralAnalysis


class US28ApplicantComparisonUnitTests(APITestCase):
    def setUp(self):
        self.uid = uuid.uuid4().hex[:8]

        # 1. Primary HR User (Room Owner)
        self.hr_owner = User.objects.create_user(
            username=f"hr_maria_{self.uid}",
            email=f"hr_maria_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Nafisa Tabassum Maria"
        )

        # 2. Other HR User (Unauthorized to access this room)
        self.other_hr = User.objects.create_user(
            username=f"other_hr_{self.uid}",
            email=f"other_hr_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.HR_MANAGER,
            full_name="Other HR Manager"
        )

        # 3. Student User (Candidate)
        self.student = User.objects.create_user(
            username=f"student_{self.uid}",
            email=f"student_{self.uid}@careerflow.demo",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Student User"
        )

        # 4. Recruitment Room (60% CV, 40% Video)
        self.room = RecruitmentRoom.objects.create(
            title="Senior Backend Engineer",
            company_name="Alpha Tech Inc.",
            department="Engineering",
            cv_weight=60,
            video_weight=40,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.hr_owner,
            skills_required=["Python", "Django", "PostgreSQL", "Docker", "AWS"]
        )

        # 5. Other Room owned by other HR
        self.other_room = RecruitmentRoom.objects.create(
            title="Frontend Specialist",
            company_name="Beta Solutions",
            department="Product",
            cv_weight=50,
            video_weight=50,
            status=RecruitmentRoom.Status.ACTIVE,
            created_by=self.other_hr
        )

        # 6. Create 4 Candidate Applications in self.room
        self.candidates = []
        self.applications = []

        candidate_data = [
            {"name": "Rahim Ahmed", "email": f"rahim_{self.uid}@demo.com", "cv": 90.0, "vid": 85.0, "final": 88.0, "eye": 92.0, "wpm": 140.0, "shortlisted": True},
            {"name": "Fatima Noor", "email": f"fatima_{self.uid}@demo.com", "cv": 80.0, "vid": 95.0, "final": 86.0, "eye": 88.0, "wpm": 150.0, "shortlisted": True},
            {"name": "Tanvir Hasan", "email": f"tanvir_{self.uid}@demo.com", "cv": 70.0, "vid": 75.0, "final": 72.0, "eye": 70.0, "wpm": 120.0, "shortlisted": False},
            {"name": "Anika Tabassum", "email": f"anika_{self.uid}@demo.com", "cv": 85.0, "vid": 80.0, "final": 83.0, "eye": 85.0, "wpm": 145.0, "shortlisted": False},
        ]

        for idx, item in enumerate(candidate_data):
            cand = User.objects.create_user(
                username=f"cand_{idx}_{self.uid}",
                email=item["email"],
                password="Password123!",
                role=User.Role.STUDENT,
                full_name=item["name"]
            )
            self.candidates.append(cand)

            # Create video & score models for realism
            video = PresentationVideo.objects.create(
                user=cand,
                original_filename=f"presentation_{idx}.mp4",
                raw_file_size=1024 * 500,
                compressed_file_size=1024 * 300,
                file_type="mp4",
                status="COMPLETED"
            )
            PresentationScore.objects.create(
                video=video,
                overall_score=int(item["vid"]),
                speech_score=int(item["vid"] - 2),
                behavioral_score=int(item["vid"] + 2),
                pace_score=85,
                eye_contact_score=int(item["eye"]),
                posture_score=80
            )
            SpeechAnalysis.objects.create(
                video=video,
                words_per_minute=item["wpm"],
                filler_word_count=idx,
                clarity_score=85
            )
            BehavioralAnalysis.objects.create(
                video=video,
                eye_contact_score=int(item["eye"]),
                posture_score=80,
                engagement_score=85
            )

            app = CandidateApplication.objects.create(
                room=self.room,
                candidate=cand,
                video=video,
                final_score=item["final"],
                cv_score=item["cv"],
                video_score=item["vid"],
                is_partial_score=False,
                is_shortlisted=item["shortlisted"],
                status=CandidateApplication.Status.COMPLETED
            )
            self.applications.append(app)

        # 7. Candidate Application in other_room
        self.foreign_cand = User.objects.create_user(
            username=f"foreign_{self.uid}",
            email=f"foreign_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Foreign Candidate"
        )
        self.foreign_app = CandidateApplication.objects.create(
            room=self.other_room,
            candidate=self.foreign_cand,
            final_score=75.0,
            cv_score=75.0,
            video_score=75.0,
            status=CandidateApplication.Status.COMPLETED
        )

        self.compare_url = f"/api/recruitment/rooms/{self.room.id}/compare-applicants/"

    def test_compare_applicants_valid_two_candidates(self):
        """
        US-28-T2: Verify comparing 2 valid candidates returns 200 OK
        with unified side-by-side comparison matrix.
        """
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id, self.applications[1].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["room_id"], self.room.id)
        self.assertEqual(data["comparison_count"], 2)
        self.assertEqual(len(data["applicants"]), 2)

        # Check candidate 0 metrics
        app0 = data["applicants"][0]
        self.assertEqual(app0["application_id"], self.applications[0].id)
        self.assertEqual(app0["candidate_name"], "Rahim Ahmed")
        self.assertEqual(app0["final_score"], 88.0)
        self.assertEqual(app0["cv_score"], 90.0)
        self.assertEqual(app0["video_score"], 85.0)
        self.assertEqual(app0["eye_contact_percent"], 92.0)
        self.assertEqual(app0["wpm"], 140.0)

        # Check differentials / best_in
        self.assertIn("final_score", app0["best_in"])
        self.assertIn("cv_score", app0["best_in"])
        self.assertIn("eye_contact", app0["best_in"])

        # Check candidate 1 metrics
        app1 = data["applicants"][1]
        self.assertEqual(app1["application_id"], self.applications[1].id)
        self.assertEqual(app1["candidate_name"], "Fatima Noor")
        self.assertEqual(app1["video_score"], 95.0)
        self.assertIn("video_score", app1["best_in"])

    def test_compare_applicants_valid_four_candidates_boundary(self):
        """
        US-28-T2 & AC#5: Verify upper boundary (exactly 4 candidates) is supported.
        """
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [app.id for app in self.applications]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["comparison_count"], 4)
        self.assertEqual(len(data["applicants"]), 4)
        self.assertEqual(data["highest_final_score"], 88.0)
        # Average of 88, 86, 72, 83 = 329 / 4 = 82.2
        self.assertAlmostEqual(data["average_final_score"], 82.2, places=1)

    def test_compare_applicants_too_few_boundary(self):
        """
        US-28-T2 & AC#5: Reject comparing fewer than 2 candidates (<2 boundary).
        """
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("application_ids", response.data)

    def test_compare_applicants_too_many_boundary(self):
        """
        US-28-T2 & AC#5: Reject comparing more than 4 candidates (>4 boundary).
        """
        # Create a 5th candidate
        cand5 = User.objects.create_user(
            username=f"cand5_{self.uid}",
            email=f"cand5_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Candidate Five"
        )
        app5 = CandidateApplication.objects.create(
            room=self.room,
            candidate=cand5,
            final_score=60.0,
            status=CandidateApplication.Status.COMPLETED
        )

        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id, self.applications[1].id, self.applications[2].id, self.applications[3].id, app5.id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("application_ids", response.data)

    def test_compare_applicants_empty_ids_rejected(self):
        """
        US-28-T2: Rejects empty application_ids list.
        """
        self.client.force_authenticate(user=self.hr_owner)
        response = self.client.post(self.compare_url, data={"application_ids": []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_applicants_duplicates_collapsing_below_minimum(self):
        """
        US-28-T2: Passing identical IDs [101, 101] should collapse to 1 unique ID and be rejected.
        """
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id, self.applications[0].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_applicants_foreign_room_application_rejected(self):
        """
        US-28-T2 & AC#6: Reject comparing applications belonging to a different room.
        """
        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id, self.foreign_app.id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_applicants_unauthorized_hr_forbidden(self):
        """
        US-28-T2 & AC#6: Another HR Manager cannot access comparison for this room.
        """
        self.client.force_authenticate(user=self.other_hr)
        payload = {
            "application_ids": [self.applications[0].id, self.applications[1].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_compare_applicants_student_forbidden(self):
        """
        US-28-T2 & AC#6: Non-HR users (students) receive 403 Forbidden.
        """
        self.client.force_authenticate(user=self.student)
        payload = {
            "application_ids": [self.applications[0].id, self.applications[1].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_compare_applicants_unauthenticated_forbidden(self):
        """
        US-28-T2 & AC#6: Unauthenticated request receives 401 Unauthorized.
        """
        self.client.logout()
        payload = {
            "application_ids": [self.applications[0].id, self.applications[1].id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_compare_applicants_missing_scores_handled_gracefully(self):
        """
        US-28-T5 & AC#5: Handles candidate with missing CV or Video scores gracefully
        without throwing null pointer exceptions.
        """
        cand_incomplete = User.objects.create_user(
            username=f"cand_incomplete_{self.uid}",
            email=f"incomplete_{self.uid}@demo.com",
            password="Password123!",
            role=User.Role.STUDENT,
            full_name="Incomplete Candidate"
        )
        app_incomplete = CandidateApplication.objects.create(
            room=self.room,
            candidate=cand_incomplete,
            final_score=None,
            cv_score=None,
            video_score=None,
            is_partial_score=False,
            status=CandidateApplication.Status.PENDING
        )

        self.client.force_authenticate(user=self.hr_owner)
        payload = {
            "application_ids": [self.applications[0].id, app_incomplete.id]
        }
        response = self.client.post(self.compare_url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data["applicants"]), 2)

        inc_app = data["applicants"][1]
        self.assertIsNone(inc_app["final_score"])
        self.assertIsNone(inc_app["cv_score"])
        self.assertIsNone(inc_app["video_score"])
        self.assertIsNone(inc_app["eye_contact_percent"])
        self.assertEqual(inc_app["score_tier"], "TIER_PENDING")
        self.assertEqual(inc_app["best_in"], [])
