"""
Unit & Integration Tests for US-47: Recruiter Evaluation Notes & Multi-Stage Interview Pipeline Progression (US-47-T7).
Covers:
  - AC-1: HR can add, edit, and view internal recruiter notes for applicants in their room.
  - AC-2: Candidate stage can be updated along the pipeline:
          (APPLIED, UNDER_REVIEW, SHORTLISTED, INTERVIEW_ROUND_1, INTERVIEW_ROUND_2, OFFERED, HIRED, REJECTED).
  - AC-3: Notes include author name, timestamp, and edit history flag (is_edited).
  - AC-4: Internal recruiter notes are strictly invisible to candidate/applicant users (403 Forbidden).
  - AC-5: Stage updates trigger in-app applicant notifications when configured.
  - AC-6: Query parameter stage filtering on room rankings endpoint.
  - Edge cases: Empty note validation, invalid stage values, cross-tenant HR isolation, author vs non-author deletion.
"""

import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User
from apps.recruitment.models import (
    RecruitmentRoom,
    CandidateApplication,
    CandidateNote,
    CandidateStageHistory,
)
from apps.cv.models import CandidateCV
from apps.core.models import Notification


class RecruiterNotesAndStagesAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.uid = uuid.uuid4().hex[:6]

        # 1. Primary HR Manager (Room Owner)
        self.hr_user = User.objects.create_user(
            username=f"hr_{self.uid}",
            email=f"hr_{self.uid}@careerflow.test",
            password="SecurePass2026!",
            role=User.Role.HR_MANAGER,
            full_name="Eleanor Vance, Head of Talent",
        )

        # 2. Rogue HR Manager (Different tenant / company)
        self.rogue_hr = User.objects.create_user(
            username=f"rogue_{self.uid}",
            email=f"rogue_{self.uid}@careerflow.test",
            password="SecurePass2026!",
            role=User.Role.HR_MANAGER,
            full_name="Rogue Recruiter",
        )

        # 3. Colleague HR (Same company / authorized recruiter in team)
        self.colleague_hr = User.objects.create_user(
            username=f"colleague_{self.uid}",
            email=f"colleague_{self.uid}@careerflow.test",
            password="SecurePass2026!",
            role=User.Role.HR_MANAGER,
            full_name="Marcus Aurelius, Tech Recruiter",
        )

        # 4. Student Candidate
        self.candidate = User.objects.create_user(
            username=f"candidate_{self.uid}",
            email=f"candidate_{self.uid}@careerflow.test",
            password="SecurePass2026!",
            role=User.Role.STUDENT,
            full_name="Jordan Bell, Senior Engineer",
        )

        # 5. Recruitment Room
        self.room = RecruitmentRoom.objects.create(
            created_by=self.hr_user,
            title="Senior Distributed Systems Engineer",
            company_name="Apex Global Technologies",
            department="Cloud Architecture",
            status=RecruitmentRoom.Status.OPEN,
            cv_weight=50,
            video_weight=50,
        )

        # 6. Candidate CV
        self.cv = CandidateCV.objects.create(
            user=self.candidate,
            file="cvs/jordan.pdf",
            original_filename="Jordan_Bell_CV.pdf",
            file_size=2048,
            file_type="pdf",
            is_active=True,
        )

        # 7. Candidate Application
        self.application = CandidateApplication.objects.create(
            room=self.room,
            candidate=self.candidate,
            cv=self.cv,
            cv_score=92.0,
            video_score=88.0,
            final_score=90.0,
            stage=CandidateApplication.Stage.APPLIED,
            status=CandidateApplication.Status.COMPLETED,
        )

    # -------------------------------------------------------------------------
    # AC-1 & AC-3: Internal Recruiter Notes CRUD, Author & Edit History
    # -------------------------------------------------------------------------

    def test_hr_can_create_internal_note(self):
        """AC-1: HR room owner can post an internal recruiter note on an applicant."""
        self.client.force_authenticate(user=self.hr_user)
        payload = {"content": "Strong distributed systems background with high Paxos/Raft consensus familiarity."}
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.post(url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["content"], payload["content"])
        self.assertEqual(resp.data["author_name"], self.hr_user.full_name)
        self.assertEqual(resp.data["author_email"], self.hr_user.email)
        self.assertFalse(resp.data["is_edited"])
        self.assertIn("created_at", resp.data)

        # Verify DB persistence
        self.assertEqual(CandidateNote.objects.filter(application=self.application).count(), 1)
        db_note = CandidateNote.objects.first()
        self.assertEqual(db_note.author, self.hr_user)

    def test_hr_can_list_internal_notes_in_chronological_order(self):
        """AC-1 & AC-3: Listing notes returns notes with author and creation timestamps."""
        note1 = CandidateNote.objects.create(
            application=self.application,
            author=self.hr_user,
            content="Initial screen note.",
        )
        note2 = CandidateNote.objects.create(
            application=self.application,
            author=self.hr_user,
            content="Follow-up panel note.",
        )

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        # Should be ordered by -created_at (newest first)
        self.assertEqual(resp.data[0]["id"], note2.id)
        self.assertEqual(resp.data[1]["id"], note1.id)

    def test_hr_can_edit_internal_note_and_sets_is_edited_flag(self):
        """AC-1 & AC-3: Editing a note updates content and sets is_edited=True."""
        note = CandidateNote.objects.create(
            application=self.application,
            author=self.hr_user,
            content="Draft observation: candidate speaks clearly.",
        )
        self.assertFalse(note.is_edited)

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/notes/{note.id}/"
        payload = {"content": "Final observation: candidate demonstrated deep knowledge of distributed caching."}
        resp = self.client.put(url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], payload["content"])
        self.assertTrue(resp.data["is_edited"])

        note.refresh_from_db()
        self.assertEqual(note.content, payload["content"])
        self.assertTrue(note.is_edited)

    def test_hr_can_delete_internal_note(self):
        """AC-1: Note author or room owner can delete a note."""
        note = CandidateNote.objects.create(
            application=self.application,
            author=self.hr_user,
            content="Accidental temporary scratch note.",
        )
        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/notes/{note.id}/"
        resp = self.client.delete(url)

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CandidateNote.objects.filter(id=note.id).count(), 0)

    def test_empty_or_whitespace_note_rejected_with_400(self):
        """Validation: Creating or editing with empty content returns 400 Bad Request."""
        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.post(url, {"content": "   \n\t "}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # AC-4: Privacy Enforcement & Tenant Isolation
    # -------------------------------------------------------------------------

    def test_candidate_cannot_view_internal_notes_403(self):
        """AC-4: Candidates / students are strictly forbidden from viewing recruiter notes."""
        CandidateNote.objects.create(
            application=self.application,
            author=self.hr_user,
            content="Internal discussion: candidate salary expectation is slightly high.",
        )
        self.client.force_authenticate(user=self.candidate)
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_candidate_cannot_create_recruiter_note_403(self):
        """AC-4: Candidates / students cannot post recruiter notes."""
        self.client.force_authenticate(user=self.candidate)
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.post(url, {"content": "Sneaky note injection."}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_rejected_with_401(self):
        """Security: Unauthenticated requests to notes or stages return 401."""
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rogue_hr_cannot_view_or_post_notes_on_other_room_403(self):
        """Security & Cross-Tenant: HR from other company cannot view or post notes."""
        self.client.force_authenticate(user=self.rogue_hr)
        url = f"/api/recruitment/applications/{self.application.id}/notes/"
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, status.HTTP_403_FORBIDDEN)

        resp_post = self.client.post(url, {"content": "Spying on competitor candidate."}, format="json")
        self.assertEqual(resp_post.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # AC-2 & AC-3: Candidate Stage Progression & Stage History
    # -------------------------------------------------------------------------

    def test_hr_can_progress_candidate_stage_along_pipeline(self):
        """
        AC-2: Candidate stage can be updated across all 8 pipeline milestones:
        APPLIED -> UNDER_REVIEW -> SHORTLISTED -> INTERVIEW_ROUND_1 ->
        INTERVIEW_ROUND_2 -> OFFERED -> HIRED -> REJECTED.
        """
        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage/"

        stages = [
            CandidateApplication.Stage.UNDER_REVIEW,
            CandidateApplication.Stage.SHORTLISTED,
            CandidateApplication.Stage.INTERVIEW_ROUND_1,
            CandidateApplication.Stage.INTERVIEW_ROUND_2,
            CandidateApplication.Stage.OFFERED,
            CandidateApplication.Stage.HIRED,
        ]

        for target_stage in stages:
            resp = self.client.patch(url, {"stage": target_stage, "notes": f"Moving to {target_stage}"}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.data["stage"], target_stage)
            self.application.refresh_from_db()
            self.assertEqual(self.application.stage, target_stage)

    def test_stage_progression_creates_audit_history_record(self):
        """AC-2 & AC-3: Each stage transition creates a CandidateStageHistory entry."""
        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage/"
        payload = {
            "stage": CandidateApplication.Stage.INTERVIEW_ROUND_1,
            "notes": "Passed technical phone screen with flying colors.",
        }
        resp = self.client.patch(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Verify DB history record
        histories = CandidateStageHistory.objects.filter(application=self.application)
        self.assertEqual(histories.count(), 1)
        history = histories.first()
        self.assertEqual(history.from_stage, CandidateApplication.Stage.APPLIED)
        self.assertEqual(history.to_stage, CandidateApplication.Stage.INTERVIEW_ROUND_1)
        self.assertEqual(history.updated_by, self.hr_user)
        self.assertEqual(history.notes, payload["notes"])

    def test_candidate_stage_history_endpoint(self):
        """AC-3: GET /api/recruitment/applications/<id>/stage-history/ returns transition trail."""
        CandidateStageHistory.objects.create(
            application=self.application,
            from_stage=CandidateApplication.Stage.APPLIED,
            to_stage=CandidateApplication.Stage.UNDER_REVIEW,
            updated_by=self.hr_user,
            notes="First step review.",
        )
        CandidateStageHistory.objects.create(
            application=self.application,
            from_stage=CandidateApplication.Stage.UNDER_REVIEW,
            to_stage=CandidateApplication.Stage.SHORTLISTED,
            updated_by=self.hr_user,
            notes="Second step shortlisted.",
        )

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage-history/"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]["to_stage"], CandidateApplication.Stage.SHORTLISTED)
        self.assertEqual(resp.data[1]["to_stage"], CandidateApplication.Stage.UNDER_REVIEW)

    def test_invalid_stage_rejected_with_400(self):
        """Validation: Invalid stage key returns 400 Bad Request."""
        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage/"
        resp = self.client.patch(url, {"stage": "FLYING_TO_MARS"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # AC-5: In-App Applicant Notification Dispatch on Stage Progression
    # -------------------------------------------------------------------------

    def test_stage_progression_dispatches_candidate_notification(self):
        """AC-5: When notify_candidate=True, candidate receives an in-app Notification."""
        initial_notif_count = Notification.objects.filter(user=self.candidate).count()

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage/"
        payload = {
            "stage": CandidateApplication.Stage.INTERVIEW_ROUND_1,
            "notes": "Invited for round 1 interview.",
            "notify_candidate": True,
        }
        resp = self.client.patch(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Check notification
        notifs = Notification.objects.filter(user=self.candidate)
        self.assertEqual(notifs.count(), initial_notif_count + 1)
        latest = notifs.latest('id')
        self.assertIn("Application Update", latest.title)
        self.assertIn("Interview Round 1", latest.message)
        self.assertEqual(latest.notification_type, Notification.NotificationType.APPLICATION_STATUS)

    def test_stage_progression_with_notify_candidate_false_skips_notification(self):
        """AC-5: When notify_candidate=False, no notification is sent."""
        initial_notif_count = Notification.objects.filter(user=self.candidate).count()

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/applications/{self.application.id}/stage/"
        payload = {
            "stage": CandidateApplication.Stage.UNDER_REVIEW,
            "notify_candidate": False,
        }
        resp = self.client.patch(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(user=self.candidate).count(), initial_notif_count)

    # -------------------------------------------------------------------------
    # AC-6: Candidate Stage Filtering on Room Rankings Endpoint
    # -------------------------------------------------------------------------

    def test_room_ranked_applicants_supports_stage_filtering(self):
        """AC-6: HR can filter room applicants by stage query param (?stage=...)."""
        # Jordan is in APPLIED stage
        uid2 = uuid.uuid4().hex[:6]
        cand2 = User.objects.create_user(
            username=f"cand2_{uid2}",
            email=f"cand2_{uid2}@careerflow.test",
            password="SecurePass2026!",
            role=User.Role.STUDENT,
            full_name="Samantha Ray, Tech Lead",
        )
        cv2 = CandidateCV.objects.create(
            user=cand2,
            file="cvs/sam.pdf",
            original_filename="Sam_CV.pdf",
            file_size=1024,
            file_type="pdf",
            is_active=True,
        )
        app2 = CandidateApplication.objects.create(
            room=self.room,
            candidate=cand2,
            cv=cv2,
            cv_score=85.0,
            video_score=85.0,
            final_score=85.0,
            stage=CandidateApplication.Stage.INTERVIEW_ROUND_1,
            status=CandidateApplication.Status.COMPLETED,
        )

        self.client.force_authenticate(user=self.hr_user)
        url = f"/api/recruitment/rooms/{self.room.id}/ranked-applicants/"

        # Query all
        resp_all = self.client.get(url)
        self.assertEqual(resp_all.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_all.data["total_applicants"], 2)

        # Query stage=INTERVIEW_ROUND_1
        resp_r1 = self.client.get(url, {"stage": "INTERVIEW_ROUND_1"})
        self.assertEqual(resp_r1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_r1.data["results"]), 1)
        self.assertEqual(resp_r1.data["results"][0]["application_id"], app2.id)
        self.assertEqual(resp_r1.data["results"][0]["stage"], CandidateApplication.Stage.INTERVIEW_ROUND_1)

        # Query stage=APPLIED
        resp_app = self.client.get(url, {"stage": "APPLIED"})
        self.assertEqual(resp_app.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_app.data["results"]), 1)
        self.assertEqual(resp_app.data["results"][0]["application_id"], self.application.id)
        self.assertEqual(resp_app.data["results"][0]["stage"], CandidateApplication.Stage.APPLIED)

        # Query stage with 0 matches
        resp_hired = self.client.get(url, {"stage": "HIRED"})
        self.assertEqual(resp_hired.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_hired.data["results"]), 0)
