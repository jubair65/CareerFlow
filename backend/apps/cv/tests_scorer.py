"""
Automated Unit and Integration Tests for US-08: CV Feedback & Scoring.
Tests:
- Formatting evaluation, section detection, and density penalties
- Keyword strength, skills density, and action verb detection
- Clarity and quantifiable impact detection (percentages, metrics, currency)
- Composite scoring logic and 0-100 bounds
- Actionable suggestions engine (exactly 3 distinct suggestions)
- REST API endpoints (/api/cv/current/feedback/, /api/cv/<id>/generate-feedback/, /api/cv/<id>/feedback/)
- RBAC and data isolation (US-36)
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User
from apps.cv.models import CandidateCV, ParsedCV, CVFeedback
from apps.core.models import DataAccessLog
from apps.cv.services.scorer import (
    CVScorer,
    default_scorer,
    generate_cv_feedback,
)


class CVScorerUnitTests(APITestCase):
    def setUp(self):
        self.scorer = CVScorer()

    def test_evaluate_formatting_all_sections_present(self):
        """Formatting score should be high when all standard sections are present with good word count."""
        sample_text = """
        John Doe - Software Engineer
        Contact: john@example.com | 555-1234 | github.com/johndoe

        Professional Summary
        Results-oriented Full Stack Engineer with 4 years of experience building web applications.

        Technical Skills
        Python, Django, React, TypeScript, PostgreSQL, Docker, Git.

        Work Experience
        Software Engineer at Acme Corp (2022 - Present)
        - Engineered scalable backend microservices serving 50k users.
        - Optimized database queries, reducing latency by 40%.

        Education
        BSc in Computer Science, University of Technology, 2021.
        """
        fmt = self.scorer.evaluate_formatting(sample_text)
        self.assertGreaterEqual(fmt.score, 85)
        self.assertIn('summary', fmt.detected_sections)
        self.assertIn('skills', fmt.detected_sections)
        self.assertIn('experience', fmt.detected_sections)
        self.assertIn('education', fmt.detected_sections)
        self.assertIn('contact', fmt.detected_sections)
        self.assertEqual(len(fmt.missing_sections), 0)
        self.assertFalse(fmt.has_dense_paragraphs)

    def test_evaluate_formatting_missing_sections(self):
        """Formatting score should penalize missing sections."""
        sparse_text = "John Doe. I am looking for a job. I know computers and programming."
        fmt = self.scorer.evaluate_formatting(sparse_text)
        self.assertLess(fmt.score, 70)
        self.assertGreater(len(fmt.missing_sections), 2)

    def test_evaluate_formatting_dense_paragraphs(self):
        """Dense paragraphs exceeding 150 words should trigger a penalty and flag."""
        dense_paragraph = "word " * 160
        text = f"Summary\n{dense_paragraph}\nSkills\nPython\nExperience\nDeveloper"
        fmt = self.scorer.evaluate_formatting(text)
        self.assertTrue(fmt.has_dense_paragraphs)

    def test_evaluate_keywords_high_density(self):
        """Resumes with diverse skills and multiple action verbs receive top keyword scores."""
        skills = ['Python', 'Django', 'React', 'Docker', 'PostgreSQL', 'TypeScript', 'Redis', 'AWS']
        text = (
            "Engineered distributed services, optimized caching layers, built REST APIs, "
            "spearheaded deployment pipelines, and deployed containerized apps."
        )
        kw = self.scorer.evaluate_keywords(text, skills)
        self.assertGreaterEqual(kw.score, 85)
        self.assertGreaterEqual(kw.skills_count, 8)
        self.assertGreaterEqual(kw.action_verb_diversity, 4)
        self.assertIn('engineered', kw.action_verbs_found)
        self.assertIn('optimized', kw.action_verbs_found)

    def test_evaluate_keywords_no_skills_or_verbs(self):
        """Resumes lacking skills or verbs receive low keyword scores."""
        kw = self.scorer.evaluate_keywords("I was a student at school and did homework.", [])
        self.assertLessEqual(kw.score, 45)

    def test_evaluate_clarity_with_quantifiable_metrics(self):
        """Presence of percentages, currency, and numerical metrics yields top clarity score."""
        text = (
            "Increased checkout throughput by 35%, boosting revenue by $150,000 annually. "
            "Supported 50k active users with 99.9% uptime, accelerating page loads by 2.5x."
        )
        clarity = self.scorer.evaluate_clarity_and_impact(text)
        self.assertGreaterEqual(clarity.score, 85)
        self.assertGreaterEqual(clarity.metrics_count, 3)
        self.assertTrue(any('%' in s for s in clarity.metric_samples))

    def test_evaluate_clarity_no_metrics(self):
        """Resumes without numbers or percentages receive lower clarity score."""
        text = "Responsible for writing code and attending meetings with teammates."
        clarity = self.scorer.evaluate_clarity_and_impact(text)
        self.assertLessEqual(clarity.score, 55)
        self.assertEqual(clarity.metrics_count, 0)

    def test_composite_score_bounds(self):
        """Composite score must always stay bounded within 0 to 100."""
        score_high = self.scorer.calculate_composite_score(100, 100, 100, 100, 100)
        self.assertEqual(score_high, 100)

        score_low = self.scorer.calculate_composite_score(0, 0, 0, 0, 0)
        self.assertEqual(score_low, 0)

        score_mid = self.scorer.calculate_composite_score(80, 70, 90, 85, 95)
        self.assertGreaterEqual(score_mid, 0)
        self.assertLessEqual(score_mid, 100)

    def test_suggestions_engine_returns_exactly_three(self):
        """Suggestions engine must return exactly 3 unique, actionable recommendations."""
        # Case 1: Sparse resume missing metrics and skills
        fmt = self.scorer.evaluate_formatting("Profile\nShort text.")
        kw = self.scorer.evaluate_keywords("Short text.", ['Python'])
        clar = self.scorer.evaluate_clarity_and_impact("Short text.")
        exp_edu = self.scorer.evaluate_experience_and_education([], [])

        suggestions = self.scorer.generate_suggestions(fmt, kw, clar, exp_edu)
        self.assertEqual(len(suggestions), 3)
        self.assertEqual(len(set(suggestions)), 3)
        # Should prioritize quantifying metrics
        self.assertTrue(any('measurable' in s.lower() or 'quantify' in s.lower() for s in suggestions))

        # Case 2: Complete, high-performing resume
        fmt2 = self.scorer.evaluate_formatting(
            "Summary\nPython engineer.\nSkills\nPython, Django, React, AWS.\n"
            "Experience\nBuilt apps for 50k users, improved latency by 30%.\n"
            "Education\nBSc CS University.\nContact\nemail@test.com"
        )
        kw2 = self.scorer.evaluate_keywords(
            "built apps, engineered APIs, optimized database, spearheaded team, automated CI",
            ['Python', 'Django', 'React', 'AWS', 'Docker', 'PostgreSQL', 'TypeScript', 'Redis']
        )
        clar2 = self.scorer.evaluate_clarity_and_impact("Improved by 30% for 50k users, saved $20k.")
        exp_edu2 = self.scorer.evaluate_experience_and_education(
            [{'title': 'Eng', 'company': 'Acme'}],
            [{'degree': 'BSc', 'institution': 'MIT'}]
        )

        suggestions2 = self.scorer.generate_suggestions(fmt2, kw2, clar2, exp_edu2)
        self.assertEqual(len(suggestions2), 3)
        self.assertEqual(len(set(suggestions2)), 3)


class CVFeedbackAPITests(APITestCase):
    def setUp(self):
        self.student_1 = User.objects.create_user(
            email='student1_feedback@careerflow.demo',
            username='student1_feedback',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Student One'
        )
        self.student_2 = User.objects.create_user(
            email='student2_feedback@careerflow.demo',
            username='student2_feedback',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Student Two'
        )
        self.hr_user = User.objects.create_user(
            email='hr_feedback@careerflow.demo',
            username='hr_feedback',
            password='Password123!',
            role=User.Role.HR_MANAGER,
            full_name='HR User'
        )

        # Create active CV for student 1
        dummy_content = b"%PDF-1.4 dummy pdf content for testing feedback"
        pdf_file = SimpleUploadedFile("resume_maria.pdf", dummy_content, content_type="application/pdf")
        self.cv_1 = CandidateCV.objects.create(
            user=self.student_1,
            file=pdf_file,
            original_filename="resume_maria.pdf",
            file_size=len(dummy_content),
            file_type="pdf",
            is_active=True,
        )

        # Create ParsedCV for student 1
        self.parsed_cv_1 = ParsedCV.objects.create(
            cv=self.cv_1,
            raw_text="""
            Professional Summary
            Passionate Software Developer with strong background in backend and cloud architectures.

            Contact
            maria@test.com | 123-456-7890 | github.com/maria

            Technical Skills
            Python, Django, PostgreSQL, Docker, React, TypeScript, Git, Redis.

            Work Experience
            Backend Engineer at TechCorp (2021 - Present)
            - Engineered payment integration handling over $250,000 in monthly transactions.
            - Optimized REST API endpoints, reducing median response latency by 32%.
            - Spearheaded automated testing coverage from 60% to 92%.

            Education
            Bachelor of Science in Computer Science, State University, 2021.
            """,
            skills=['Python', 'Django', 'PostgreSQL', 'Docker', 'React', 'TypeScript', 'Git', 'Redis'],
            education=[{'degree': 'BSc Computer Science', 'institution': 'State University', 'year': '2021'}],
            experience=[{'title': 'Backend Engineer', 'company': 'TechCorp', 'duration': '2021 - Present'}],
        )

    def test_generate_feedback_endpoint_success(self):
        """Student can successfully trigger CV feedback generation (US-08-T5)."""
        self.client.force_authenticate(user=self.student_1)
        url = reverse('cv:cv_generate_feedback', kwargs={'cv_id': self.cv_1.id})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'CV feedback generated successfully.')

        feedback = response.data['feedback']
        self.assertGreaterEqual(feedback['overall_score'], 75)
        self.assertGreaterEqual(feedback['formatting_score'], 80)
        self.assertGreaterEqual(feedback['clarity_score'], 80)
        self.assertGreaterEqual(feedback['keyword_strength_score'], 80)
        self.assertEqual(len(feedback['suggestions']), 3)
        self.assertIn('signal_breakdown', feedback)
        self.assertIn('extracted_skills', feedback)
        self.assertEqual(len(feedback['extracted_skills']), 8)

        # Verify database record
        db_fb = CVFeedback.objects.get(cv=self.cv_1)
        self.assertEqual(db_fb.overall_score, feedback['overall_score'])

        # Verify audit log recorded (US-36)
        log = DataAccessLog.objects.filter(user=self.student_1, action=DataAccessLog.Action.VIEW).first()
        self.assertIsNotNone(log)

    def test_current_cv_feedback_endpoint(self):
        """Current CV feedback endpoint returns feedback for active CV (or generates if missing)."""
        self.client.force_authenticate(user=self.student_1)
        url = reverse('cv:cv_current_feedback')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('feedback', response.data)
        self.assertEqual(response.data['cv_id'], self.cv_1.id)
        self.assertGreater(response.data['feedback']['overall_score'], 0)

    def test_current_cv_feedback_no_cv_uploaded(self):
        """Current CV feedback endpoint gracefully handles student with no uploaded CV."""
        self.client.force_authenticate(user=self.student_2)
        url = reverse('cv:cv_current_feedback')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['feedback'])

    def test_feedback_detail_endpoint(self):
        """Detail feedback endpoint returns existing feedback for CV."""
        # Generate feedback first
        generate_cv_feedback(self.cv_1)

        self.client.force_authenticate(user=self.student_1)
        url = reverse('cv:cv_feedback_detail', kwargs={'cv_id': self.cv_1.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cv'], self.cv_1.id)
        self.assertEqual(len(response.data['suggestions']), 3)

    def test_rbac_student_cannot_access_other_student_feedback(self):
        """Student 2 cannot generate or view feedback for Student 1's CV (403 Forbidden)."""
        self.client.force_authenticate(user=self.student_2)
        generate_url = reverse('cv:cv_generate_feedback', kwargs={'cv_id': self.cv_1.id})
        detail_url = reverse('cv:cv_feedback_detail', kwargs={'cv_id': self.cv_1.id})

        gen_resp = self.client.post(generate_url)
        self.assertEqual(gen_resp.status_code, status.HTTP_403_FORBIDDEN)

        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_denied(self):
        """Unauthenticated requests are rejected with 401 Unauthorized."""
        url = reverse('cv:cv_current_feedback')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
