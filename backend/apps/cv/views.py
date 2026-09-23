import os
from django.db import transaction
from rest_framework import status, permissions, parsers
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import CandidateCV
from .serializers import CandidateCVSerializer
from apps.authentication.permissions import IsStudent
from apps.core.models import DataAccessLog


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
