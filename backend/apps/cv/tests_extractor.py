import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
import docx

from apps.authentication.models import User
from apps.cv.models import CandidateCV
from apps.cv.services.contracts import EducationItem, ExperienceItem, ExtractionResult
from apps.cv.services.text_extractor import (
    clean_extracted_text,
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text,
)
from apps.cv.services.skill_extractor import SkillExtractor, extract_skills, get_skill_extractor
from apps.cv.services.pipeline import CVExtractionPipeline, extract_cv_data


class ContractsTests(TestCase):
    def test_education_item(self):
        item = EducationItem(degree='BSc Computer Science', institution='MIT', year='2024', grade='3.9')
        d = item.to_dict()
        self.assertEqual(d['degree'], 'BSc Computer Science')
        self.assertEqual(d['institution'], 'MIT')
        self.assertEqual(d['year'], '2024')
        self.assertEqual(d['grade'], '3.9')

    def test_experience_item(self):
        item = ExperienceItem(title='Software Engineer', company='Acme', duration='2 years', years_count=2.0)
        d = item.to_dict()
        self.assertEqual(d['title'], 'Software Engineer')
        self.assertEqual(d['company'], 'Acme')
        self.assertEqual(d['years_count'], 2.0)

    def test_extraction_result(self):
        res = ExtractionResult(raw_text='Test resume', skills=['Python'], word_count=2)
        d = res.to_dict()
        self.assertEqual(d['raw_text'], 'Test resume')
        self.assertEqual(d['skills'], ['Python'])
        self.assertEqual(d['word_count'], 2)
        self.assertTrue(d['success'])
        self.assertIsNone(d['error_message'])


class TextExtractorTests(TestCase):
    def test_clean_extracted_text_normalizes_whitespace_and_bullets(self):
        dirty = "\u2022 Item 1  with   spaces\n\u2023 Item 2\n\n\n\n\nItem 3 with non-breaking\u00a0space"
        cleaned = clean_extracted_text(dirty)
        self.assertIn('- Item 1 with spaces', cleaned)
        self.assertIn('- Item 2', cleaned)
        self.assertIn('Item 3 with non-breaking space', cleaned)
        self.assertNotIn('\n\n\n', cleaned)

    def test_clean_extracted_text_empty(self):
        self.assertEqual(clean_extracted_text(None), '')
        self.assertEqual(clean_extracted_text(''), '')

    def test_docx_text_extraction_paragraphs_and_tables(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_path = f.name

        try:
            doc = docx.Document()
            doc.add_heading('John Candidate', 0)
            doc.add_paragraph('Full-stack developer with 5 years experience.')
            table = doc.add_table(rows=1, cols=2)
            table.rows[0].cells[0].text = 'Skills: Python, Django'
            table.rows[0].cells[1].text = 'Location: Dhaka'
            doc.save(docx_path)

            extracted = extract_text_from_docx(docx_path)
            self.assertIn('John Candidate', extracted)
            self.assertIn('Full-stack developer with 5 years experience.', extracted)
            self.assertIn('Skills: Python, Django', extracted)
            self.assertIn('Location: Dhaka', extracted)
        finally:
            if os.path.exists(docx_path):
                os.unlink(docx_path)

    @patch('pdfplumber.open')
    def test_pdf_text_extraction_with_mock(self, mock_open):
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = 'Page 1: Jane Doe, Software Engineer'
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = 'Page 2: Education: Stanford University'
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__.return_value = mock_pdf

        mock_open.return_value = mock_pdf

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            pdf_path = f.name

        try:
            extracted = extract_text_from_pdf(pdf_path)
            self.assertIn('Page 1: Jane Doe, Software Engineer', extracted)
            self.assertIn('Page 2: Education: Stanford University', extracted)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_extract_text_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract_text('non_existent_file.pdf')

    def test_extract_text_unsupported_format(self):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'sample text')
            txt_path = f.name

        try:
            with self.assertRaises(ValueError):
                extract_text(txt_path)
        finally:
            if os.path.exists(txt_path):
                os.unlink(txt_path)


class SkillExtractorTests(TestCase):
    def setUp(self):
        self.extractor = SkillExtractor()

    def test_extract_standard_tech_skills(self):
        text = 'Extensive experience building web applications using Python, Django, React, and PostgreSQL.'
        skills = self.extractor.extract_skills(text)
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('React', skills)
        self.assertIn('PostgreSQL', skills)

    def test_extract_symbol_skills(self):
        text = 'Strong knowledge in C++, C#, .NET Core, Node.js, and CI/CD automation.'
        skills = self.extractor.extract_skills(text)
        self.assertIn('C++', skills)
        self.assertIn('C#', skills)
        self.assertIn('.NET Core', skills)
        self.assertIn('Node.js', skills)
        self.assertIn('CI/CD', skills)

    def test_canonical_synonyms_and_aliases(self):
        text = 'Proficient in React.js, Golang, Postgres, and Tailwind CSS.'
        skills = self.extractor.extract_skills(text)
        self.assertIn('React', skills)
        self.assertIn('Go', skills)
        self.assertIn('PostgreSQL', skills)
        self.assertIn('TailwindCSS', skills)

    def test_avoid_false_positives_for_single_letter_skills(self):
        text = 'Candidate was clear, created clever code for the company car club.'
        skills = self.extractor.extract_skills(text)
        # Should NOT match single letter 'C' from words starting with 'c'
        self.assertNotIn('C', skills)

        # But should match when explicitly listed as language
        text_with_c = 'Programming languages: Python, C, C++, Java'
        skills_with_c = self.extractor.extract_skills(text_with_c)
        self.assertIn('C', skills_with_c)
        self.assertIn('Python', skills_with_c)
        self.assertIn('C++', skills_with_c)
        self.assertIn('Java', skills_with_c)

    def test_extract_skills_by_category(self):
        text = 'Skilled in Python, Docker, Redis, and Machine Learning.'
        by_category = self.extractor.extract_skills_by_category(text)
        self.assertIn('programming_languages', by_category)
        self.assertIn('Python', by_category['programming_languages'])
        self.assertIn('cloud_and_devops', by_category)
        self.assertIn('Docker', by_category['cloud_and_devops'])
        self.assertIn('databases', by_category)
        self.assertIn('Redis', by_category['databases'])
        self.assertIn('data_science_and_ai', by_category)
        self.assertIn('Machine Learning', by_category['data_science_and_ai'])

    def test_extract_skills_with_counts(self):
        text = 'Python developer with strong Python backend and Python script automation using Django.'
        counts = self.extractor.extract_skills_with_counts(text)
        self.assertEqual(counts.get('Python'), 3)
        self.assertEqual(counts.get('Django'), 1)


class CVExtractionPipelineTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email='bonny_dev@careerflow.demo',
            username='bonny_dev',
            password='Password123!',
            role=User.Role.STUDENT,
            full_name='Bonny Developer'
        )

    def test_pipeline_with_docx_file(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_path = f.name

        try:
            doc = docx.Document()
            doc.add_heading('Bonny - Backend Engineer', 0)
            doc.add_paragraph('Expert in Python, FastAPI, Docker, and PostgreSQL.')
            doc.save(docx_path)

            pipeline = CVExtractionPipeline()
            result = pipeline.process_file(docx_path)

            self.assertTrue(result.success)
            self.assertGreater(result.word_count, 0)
            self.assertIn('Python', result.skills)
            self.assertIn('FastAPI', result.skills)
            self.assertIn('Docker', result.skills)
            self.assertIn('PostgreSQL', result.skills)
        finally:
            if os.path.exists(docx_path):
                os.unlink(docx_path)

    def test_pipeline_with_candidate_cv_model(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_path = f.name

        try:
            doc = docx.Document()
            doc.add_heading('Model Candidate', 0)
            doc.add_paragraph('Experienced with Django, Redis, and Git.')
            doc.save(docx_path)

            with open(docx_path, 'rb') as f_read:
                cv_file = SimpleUploadedFile('test_resume.docx', f_read.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

            candidate_cv = CandidateCV.objects.create(
                user=self.student,
                file=cv_file,
                original_filename='test_resume.docx',
                file_size=1024,
                file_type='docx',
                is_active=True
            )

            pipeline = CVExtractionPipeline()
            result = pipeline.process_candidate_cv(candidate_cv)

            self.assertTrue(result.success)
            self.assertIn('Django', result.skills)
            self.assertIn('Redis', result.skills)
            self.assertIn('Git', result.skills)
        finally:
            if os.path.exists(docx_path):
                os.unlink(docx_path)

    def test_pipeline_with_pluggable_entity_extractor(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            docx_path = f.name

        try:
            doc = docx.Document()
            doc.add_paragraph('Sample CV with education and experience.')
            doc.save(docx_path)

            def mock_person2_entities(text):
                return {
                    'education': [{'degree': 'BSc Software Engineering', 'institution': 'BRAC University'}],
                    'experience': [{'title': 'Junior Dev', 'company': 'InnoTech'}]
                }

            pipeline = CVExtractionPipeline(entity_extractor=mock_person2_entities)
            result = pipeline.process_file(docx_path)

            self.assertTrue(result.success)
            self.assertEqual(len(result.education), 1)
            self.assertEqual(result.education[0]['degree'], 'BSc Software Engineering')
            self.assertEqual(len(result.experience), 1)
            self.assertEqual(result.experience[0]['company'], 'InnoTech')
        finally:
            if os.path.exists(docx_path):
                os.unlink(docx_path)

    def test_pipeline_file_not_found(self):
        pipeline = CVExtractionPipeline()
        result = pipeline.process_file('imaginary_non_existent.pdf')
        self.assertFalse(result.success)
        self.assertIn('File not found', result.error_message)
