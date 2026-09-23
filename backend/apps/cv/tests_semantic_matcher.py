import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.cv.models import CandidateCV, ParsedCV, JobRequirement, CVJobMatch
from apps.cv.services.semantic_matcher import CVJobSemanticMatcher, match_cv_to_job


class CVJobSemanticMatcherTests(APITestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            email='student_matcher_test@careerflow.demo',
            username='student_matcher_test',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Test Candidate'
        )
        self.hr_user = User.objects.create_user(
            email='hr_matcher_test@careerflow.demo',
            username='hr_matcher_test',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='Test HR Manager'
        )

        # Create active candidate CV
        dummy_file = SimpleUploadedFile(
            'frontend_resume.pdf',
            b'%PDF-1.4 React Python Figma Accessibility JavaScript HTML CSS Django REST framework',
            content_type='application/pdf'
        )
        self.cv = CandidateCV.objects.create(
            user=self.student_user,
            file=dummy_file,
            original_filename='frontend_resume.pdf',
            file_size=1024,
            file_type='pdf',
            is_active=True,
        )

        # Create parsed data
        self.parsed_cv = ParsedCV.objects.create(
            cv=self.cv,
            raw_text="Experienced Senior Frontend Developer skilled in React, JavaScript, HTML, CSS, Figma, and Web Accessibility. Led cross-functional collaboration with product design team.",
            skills=['React', 'JavaScript', 'Figma', 'HTML', 'CSS', 'Accessibility', 'Python'],
            education=[{'degree': 'B.S. Computer Science', 'institution': 'MIT', 'year': '2022'}],
            experience=[{'title': 'Senior Frontend Developer', 'company': 'Tech Corp', 'years_count': 4.0}]
        )

        self.match_url = reverse('cv:cv_match_compute')
        self.current_match_url = reverse('cv:cv_current_match')
        self.hr_matches_url = reverse('cv:cv_hr_matches')

    def test_semantic_matcher_service_calculation(self):
        """US-09: Test direct service semantic match score calculation (0-100)."""
        matcher = CVJobSemanticMatcher()
        result = matcher.evaluate_match(
            cv=self.cv,
            job_title='Senior Frontend Engineer',
            job_description='Looking for a Senior Frontend Engineer proficient in React, Figma, JavaScript, and Accessibility.',
            required_skills=['React', 'JavaScript', 'Figma', 'Accessibility', 'Redux']
        )

        self.assertGreaterEqual(result.match_score, 0)
        self.assertLessEqual(result.match_score, 100)
        self.assertGreater(result.keyword_coverage, 50)
        self.assertIn('React', result.skills_matched)
        self.assertIn('Figma', result.skills_matched)
        self.assertIn('Redux', result.skills_missing)
        self.assertIn('domain_craft', result.category_scores)
        self.assertIn('collaboration', result.category_scores)

    def test_compute_match_api_endpoint(self):
        """US-09: POST /api/cv/match/ computes and persists match result."""
        self.client.force_authenticate(user=self.student_user)
        payload = {
            'job_title': 'Frontend Developer',
            'company': 'Aurora Labs',
            'job_description': 'We need a Frontend Developer with React and Figma expertise.',
            'required_skills': ['React', 'Figma', 'TypeScript']
        }

        response = self.client.post(self.match_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('match', response.data)
        match_data = response.data['match']
        self.assertEqual(match_data['job_title'], 'Frontend Developer')
        self.assertGreaterEqual(match_data['match_score'], 0)
        self.assertLessEqual(match_data['match_score'], 100)
        self.assertIn('React', match_data['skills_matched'])

        # Verify DB persistence
        match_in_db = CVJobMatch.objects.get(id=match_data['id'])
        self.assertEqual(match_in_db.cv, self.cv)
        self.assertEqual(match_in_db.job_title, 'Frontend Developer')

    def test_get_current_match_api_endpoint(self):
        """US-09: GET /api/cv/match/current/ returns active CV's match score."""
        self.client.force_authenticate(user=self.student_user)

        response = self.client.get(self.current_match_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['match'])
        self.assertIn('match_score', response.data['match'])

    def test_hr_applicant_matches_endpoint(self):
        """US-09-T6: HR manager can view applicants' CV match scores."""
        # Create match record
        match_cv_to_job(
            cv=self.cv,
            job_title='Senior Product Designer',
            job_description='Product designer role requirement',
            required_skills=['Figma', 'React']
        )

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(self.hr_matches_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['candidate_email'], self.student_user.email)
