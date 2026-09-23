import os
import logging
from django.db import transaction
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CandidateCV, ParsedCV, CVFeedback, JobRequirement, CVJobMatch
from .serializers import (
    CandidateCVSerializer, ParsedCVSerializer, CVFeedbackSerializer,
    JobRequirementSerializer, CVJobMatchSerializer, JobMatchRequestSerializer
)
from .services.pipeline import CVExtractionPipeline
from .services.scorer import generate_cv_feedback
from .services.semantic_matcher import match_cv_to_job
from apps.authentication.permissions import IsStudent, IsHRManager
from apps.core.models import DataAccessLog

logger = logging.getLogger(__name__)



class CVUploadView(APIView):
    """
    POST /api/cv/upload/
    Upload a candidate's CV (PDF or DOCX, max 10MB).
    Deactivates any previous CV for this candidate, sets the newly uploaded CV as active,
    and logs the action in DataAccessLog (US-36).
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file uploaded. Please attach a CV file under the "file" field.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CandidateCVSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')

        with transaction.atomic():
            # 1. Deactivate prior active CVs for this student
            CandidateCV.objects.filter(user=request.user, is_active=True).update(is_active=False)

            # 2. Save new active CV
            cv = CandidateCV.objects.create(
                user=request.user,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=ext,
                is_active=True,
            )

            # 3. Log data upload for audit security (US-36)
            DataAccessLog.objects.create(
                user=request.user,
                resource_path=cv.file.name,
                action=DataAccessLog.Action.UPLOAD,
                status=DataAccessLog.Status.GRANTED,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # 4. Auto-trigger extraction pipeline (US-07) and feedback scoring (US-08)
            try:
                pipeline = CVExtractionPipeline()
                result = pipeline.process_candidate_cv(cv)
                if result.success and result.raw_text:
                    ParsedCV.objects.update_or_create(
                        cv=cv,
                        defaults={
                            'raw_text': result.raw_text,
                            'skills': result.skills,
                            'education': result.education,
                            'experience': result.experience,
                        }
                    )
                    # 5. Auto-trigger feedback scoring (US-08)
                    try:
                        generate_cv_feedback(cv)
                    except Exception as fb_err:
                        logger.warning(f"Auto-feedback scoring after upload skipped: {fb_err}")
            except Exception as parse_err:
                logger.warning(f"Auto-extraction after upload skipped: {parse_err}")

        response_serializer = CandidateCVSerializer(cv)
        return Response(
            {
                'message': 'CV uploaded successfully.',
                'cv': response_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )


class CurrentCVView(APIView):
    """
    GET /api/cv/current/
    Fetch the candidate's currently active CV.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        cv = CandidateCV.objects.filter(user=request.user, is_active=True).first()
        if not cv:
            return Response({'cv': None}, status=status.HTTP_200_OK)

        serializer = CandidateCVSerializer(cv)
        return Response({'cv': serializer.data}, status=status.HTTP_200_OK)


class CVHistoryView(APIView):
    """
    GET /api/cv/history/
    Retrieve all historical CV versions uploaded by the candidate.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        cvs = CandidateCV.objects.filter(user=request.user).order_by('-uploaded_at')
        serializer = CandidateCVSerializer(cvs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CVParseView(APIView):
    """
    POST /api/cv/<cv_id>/parse/
    Parse candidate CV, extracting text, skills, education, and experience (US-07).
    Stores results in ParsedCV model and logs data access (US-36).
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request, cv_id):
        cv = CandidateCV.objects.filter(id=cv_id).first()
        if not cv:
            return Response(
                {'error': f'CV with id {cv_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if cv.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to parse this CV document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        pipeline = CVExtractionPipeline()
        result = pipeline.process_candidate_cv(cv)

        if not result.success:
            return Response(
                {
                    'error': 'CV parsing failed.',
                    'details': result.error_message,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        with transaction.atomic():
            parsed_cv, created = ParsedCV.objects.update_or_create(
                cv=cv,
                defaults={
                    'raw_text': result.raw_text,
                    'skills': result.skills,
                    'education': result.education,
                    'experience': result.experience,
                }
            )

            DataAccessLog.objects.create(
                user=request.user,
                resource_path=cv.file.name,
                action=DataAccessLog.Action.VIEW,
                status=DataAccessLog.Status.GRANTED,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # Auto-update CV feedback upon parsing
            try:
                generate_cv_feedback(cv)
            except Exception as fb_err:
                logger.warning(f"Auto-feedback update after parse skipped: {fb_err}")

        serializer = ParsedCVSerializer(parsed_cv)
        return Response(
            {
                'message': 'CV parsed and extracted successfully.',
                'parsed_cv': serializer.data,
                'is_scanned': result.is_scanned,
                'warning': result.error_message if result.is_scanned else None,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class ParsedCVDetailView(APIView):
    """
    GET /api/cv/<cv_id>/parsed/
    Retrieve parsed data (skills, education, experience, raw_text) for a CV (US-07-T5).
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, cv_id):
        cv = CandidateCV.objects.filter(id=cv_id).first()
        if not cv:
            return Response(
                {'error': f'CV with id {cv_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if cv.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to access parsed data for this CV.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            parsed_cv = cv.parsed_data
        except ParsedCV.DoesNotExist:
            return Response(
                {'error': 'Parsed data not found for this CV. Please trigger extraction first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ParsedCVSerializer(parsed_cv)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CVFeedbackGenerateView(APIView):
    """
    POST /api/cv/<cv_id>/generate-feedback/
    Generates or recalculates automated CV feedback, rubric scoring, and actionable recommendations (US-08).
    Logs data access for audit security (US-36).
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request, cv_id):
        cv = CandidateCV.objects.filter(id=cv_id).first()
        if not cv:
            return Response(
                {'error': f'CV with id {cv_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if cv.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to evaluate this CV document.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            feedback = generate_cv_feedback(cv)

            DataAccessLog.objects.create(
                user=request.user,
                resource_path=cv.file.name,
                action=DataAccessLog.Action.VIEW,
                status=DataAccessLog.Status.GRANTED,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            serializer = CVFeedbackSerializer(feedback)
            return Response(
                {
                    'message': 'CV feedback generated successfully.',
                    'feedback': serializer.data,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error generating CV feedback for CV {cv_id}: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Failed to generate CV feedback.',
                    'details': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentCVFeedbackView(APIView):
    """
    GET /api/cv/current/feedback/
    Retrieve automated CV feedback for the currently active CV of the logged-in candidate.
    If feedback does not exist yet, it is calculated automatically.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        cv = CandidateCV.objects.filter(user=request.user, is_active=True).first()
        if not cv:
            return Response(
                {
                    'feedback': None,
                    'message': 'No active CV uploaded yet. Please upload a CV to view feedback.'
                },
                status=status.HTTP_200_OK
            )

        feedback = getattr(cv, 'feedback', None)
        if not feedback:
            try:
                feedback = CVFeedback.objects.filter(cv=cv).first()
            except Exception:
                feedback = None

        if not feedback:
            try:
                feedback = generate_cv_feedback(cv)
            except Exception as e:
                logger.error(f"Error auto-generating feedback for active CV: {str(e)}", exc_info=True)
                return Response(
                    {'error': 'Failed to calculate feedback for current CV.', 'details': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        serializer = CVFeedbackSerializer(feedback)
        return Response(
            {
                'cv_id': cv.id,
                'feedback': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class CVFeedbackDetailView(APIView):
    """
    GET /api/cv/<cv_id>/feedback/
    Retrieve automated CV feedback for a specific CV version.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request, cv_id):
        cv = CandidateCV.objects.filter(id=cv_id).first()
        if not cv:
            return Response(
                {'error': f'CV with id {cv_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if cv.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view feedback for this CV.'},
                status=status.HTTP_403_FORBIDDEN
            )

        feedback = getattr(cv, 'feedback', None)
        if not feedback:
            try:
                feedback = CVFeedback.objects.filter(cv=cv).first()
            except Exception:
                feedback = None

        if not feedback:
            try:
                feedback = generate_cv_feedback(cv)
            except Exception as e:
                return Response(
                    {'error': 'Feedback not generated yet for this CV.', 'details': str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = CVFeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CVJobMatchComputeView(APIView):
    """
    POST /api/cv/match/
    Compute semantic similarity score between candidate's active CV and target job brief (US-09).
    Accepts job_title, job_description, required_skills, or job_id.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def post(self, request):
        serializer = JobMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cv = CandidateCV.objects.filter(user=request.user, is_active=True).first()
        if not cv:
            return Response(
                {'error': 'No active CV uploaded yet. Please upload a CV first in Candidate Studio.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        job_instance = None
        if data.get('job_id'):
            job_instance = JobRequirement.objects.filter(id=data['job_id']).first()

        job_title = data.get('job_title') or (job_instance.title if job_instance else 'Product Designer')
        job_description = data.get('job_description') or (job_instance.description if job_instance else '')
        required_skills = data.get('required_skills') or (job_instance.required_skills if job_instance else [])

        try:
            match_record = match_cv_to_job(
                cv=cv,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                job_instance=job_instance
            )

            # Audit log (US-36)
            DataAccessLog.objects.create(
                user=request.user,
                resource_path=f"cv_match/{cv.id}/{job_title[:30]}",
                action=DataAccessLog.Action.VIEW,
                status=DataAccessLog.Status.GRANTED,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            response_serializer = CVJobMatchSerializer(match_record)
            return Response(
                {
                    'message': 'CV semantic match score evaluated successfully.',
                    'match': response_serializer.data,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error computing CV-job semantic match: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to calculate CV-job match.', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CurrentCVJobMatchView(APIView):
    """
    GET /api/cv/match/current/
    Fetch candidate's active CV latest job match result (US-09).
    If none exists, automatically computes match against standard role requirements.
    """
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get(self, request):
        cv = CandidateCV.objects.filter(user=request.user, is_active=True).first()
        if not cv:
            return Response({'match': None, 'message': 'No active CV found.'}, status=status.HTTP_200_OK)

        match_record = CVJobMatch.objects.filter(cv=cv).order_by('-updated_at').first()
        if not match_record:
            # Generate default initial match evaluation
            try:
                match_record = match_cv_to_job(
                    cv=cv,
                    job_title='Product Designer',
                    job_description='Looking for a product designer with Figma, product strategy, accessibility, and user research skills.',
                    required_skills=['Figma', 'Product Strategy', 'User Research', 'Accessibility', 'Systems Thinking']
                )
            except Exception as e:
                logger.error(f"Error generating initial match: {str(e)}")
                return Response({'match': None}, status=status.HTTP_200_OK)

        serializer = CVJobMatchSerializer(match_record)
        return Response({'match': serializer.data}, status=status.HTTP_200_OK)


class HRApplicantMatchesView(APIView):
    """
    GET /api/cv/hr/matches/
    Retrieve candidate CV match scores across applicants for HR manager view (US-09-T6).
    """
    permission_classes = [permissions.IsAuthenticated, IsHRManager]

    def get(self, request):
        # Fetch active CV matches
        matches = CVJobMatch.objects.select_related('cv', 'cv__user').order_by('-match_score')
        serializer = CVJobMatchSerializer(matches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



