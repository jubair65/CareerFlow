import os
import logging
from django.db import transaction
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CandidateCV, ParsedCV
from .serializers import CandidateCVSerializer, ParsedCVSerializer
from .services.pipeline import CVExtractionPipeline
from apps.authentication.permissions import IsStudent
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

            # 4. Auto-trigger extraction pipeline (US-07)
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

