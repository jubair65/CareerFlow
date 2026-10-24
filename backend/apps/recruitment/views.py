from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RecruitmentRoom, ClientCompany
from .serializers import (
    RecruitmentRoomSerializer,
    RoomRequirementsSerializer,
    RoomWeightingSerializer,
    RoomShareLinkSerializer,
    PublicRoomDetailsSerializer,
    ApplicantCvScoreSerializer,
    RoomCvScoresResponseSerializer,
    CalculateScoresResponseSerializer,
    CandidateApplicationScoreSerializer,
    RankedApplicantsResponseSerializer,
    RoomShortlistCriteriaSerializer,
    ShortlistedApplicantItemSerializer,
    RoomShortlistResponseSerializer,
    CandidateDecisionSubmitSerializer,
    CandidateReviewDetailSerializer,
    CandidateDecisionResponseSerializer,
    ApplicantScoreBreakdownSerializer,
    ApplicantComparisonRequestSerializer,
    ApplicantComparisonResponseSerializer,
    ClientCompanySerializer,
    ClientCompanyStatsSerializer,
)
from .permissions import (
    IsHRManager,
    IsRoomOwner,
    IsApplicationRoomOwner,
    IsAgencyAdmin,
    IsClientAgencyOwner,
)
from .services.review_service import (
    get_candidate_review_data,
    record_candidate_review_decision,
)
from .services.breakdown_service import (
    get_applicant_score_breakdown,
)
from .services.comparison_service import (
    compare_room_applicants,
)
from .services.matcher_bridge import (
    sync_room_to_job_requirement,
    get_room_applicants_cv_scores,
    get_applicant_cv_score_data,
)
from .services.scoring_service import (
    calculate_application_score,
    calculate_room_applicant_scores,
)
from .services.ranking_service import get_ranked_room_applicants
from .services.shortlisting_service import (
    evaluate_room_shortlist,
    validate_shortlisting_criteria,
)
from .tokens import (
    generate_secure_share_token,
    validate_share_token,
    build_share_url,
    is_token_expired,
)
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from apps.cv.models import CandidateCV, ParsedCV
from apps.presentation.models import PresentationVideo
from apps.cv.services.pipeline import default_pipeline
from apps.presentation.services.pipeline_manager import PipelineManager
from .models import CandidateApplication

User = get_user_model()


class RecruitmentRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD API for HR Recruitment Rooms (US-18, US-19, US-20).
    Strictly isolated so HR Managers can only view and manage their own rooms.
    """
    serializer_class = RecruitmentRoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsHRManager, IsRoomOwner]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or user.role != 'HR_MANAGER':
            return RecruitmentRoom.objects.none()
        return RecruitmentRoom.objects.filter(created_by=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Recruitment room created successfully.",
                "room": serializer.data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {
                "message": "Recruitment room updated successfully.",
                "room": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='requirements')
    def requirements(self, request, pk=None):
        """
        US-19-T2: Manage job role details, experience level, requirements text,
        and required skill tags for a Room.
        """
        room = self.get_object()

        if request.method == 'GET':
            serializer = RoomRequirementsSerializer(room)
            return Response(
                {
                    "room_id": room.id,
                    "title": room.title,
                    "company_name": room.company_name,
                    "requirements": serializer.data,
                    "skill_names": room.get_skill_names(),
                },
                status=status.HTTP_200_OK
            )

        partial = (request.method == 'PATCH')
        serializer = RoomRequirementsSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_room = serializer.save()

        # US-19-T5: Synchronize with CV semantic matching module
        try:
            sync_room_to_job_requirement(updated_room)
        except Exception as e:
            # Non-blocking sync log
            pass

        full_serializer = RecruitmentRoomSerializer(updated_room, context={'request': request})
        return Response(
            {
                "message": "Job role and requirements updated successfully.",
                "room": full_serializer.data,
                "requirements": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='weighting')
    def weighting(self, request, pk=None):
        """
        US-20-T2: Configure evaluation weighting (CV weight % vs Video weight %) for a Room.
        Ensures weights are integers within 0-100 and total exactly 100%.
        """
        room = self.get_object()

        if request.method == 'GET':
            serializer = RoomWeightingSerializer(room)
            return Response(
                {
                    "room_id": room.id,
                    "title": room.title,
                    "company_name": room.company_name,
                    "cv_weight": room.cv_weight,
                    "video_weight": room.video_weight,
                    "weighting": serializer.data,
                },
                status=status.HTTP_200_OK
            )

        partial = (request.method == 'PATCH')
        serializer = RoomWeightingSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_room = serializer.save()

        # US-23-T5: Recalculate applicant scores with the newly configured weights
        try:
            calculate_room_applicant_scores(updated_room)
        except Exception:
            pass

        full_serializer = RecruitmentRoomSerializer(updated_room, context={'request': request})
        return Response(
            {
                "message": "Evaluation weighting updated successfully.",
                "room": full_serializer.data,
                "weighting": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get', 'post'], url_path='link')
    def link(self, request, pk=None):
        """
        US-21-T2: Retrieve or generate shareable application link for a Room.
        GET / POST /api/recruitment/rooms/{id}/link/
        """
        room = self.get_object()

        # If room does not have a token yet, generate one
        if not room.share_token:
            room.share_token = generate_secure_share_token()
            room.save(update_fields=['share_token', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Shareable link retrieved successfully.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/deactivate')
    def deactivate_link(self, request, pk=None):
        """
        US-21-T5: Deactivate shareable link, immediately invalidating candidate access.
        POST /api/recruitment/rooms/{id}/link/deactivate/
        """
        room = self.get_object()
        room.link_is_active = False
        room.save(update_fields=['link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been deactivated.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/activate')
    def activate_link(self, request, pk=None):
        """
        US-21-T5: Reactivate an existing shareable link.
        POST /api/recruitment/rooms/{id}/link/activate/
        """
        room = self.get_object()
        room.link_is_active = True
        room.save(update_fields=['link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been activated.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='link/regenerate')
    def regenerate_link(self, request, pk=None):
        """
        US-21-T5: Regenerate a new cryptographically secure token, immediately
        invalidating the previous token and enabling candidate access.
        POST /api/recruitment/rooms/{id}/link/regenerate/
        """
        room = self.get_object()
        room.share_token = generate_secure_share_token()
        room.link_is_active = True
        room.save(update_fields=['share_token', 'link_is_active', 'updated_at'])

        serializer = RoomShareLinkSerializer(room, context={'request': request})
        return Response(
            {
                "message": "Application link has been regenerated with a new secure token.",
                "link": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='cv-scores')
    def cv_scores(self, request, pk=None):
        """
        US-10-T2 & US-10-T5: View applicants' CV Match Scores and breakdown for this Room.
        Strictly enforces HR ownership (only the room owner HR manager can access).
        Query params:
          - search: filter by candidate name, email, or skill
          - min_score: filter candidates by minimum match score
        """
        room = self.get_object()
        search_query = request.query_params.get('search')
        min_score_param = request.query_params.get('min_score')
        min_score = int(min_score_param) if min_score_param and min_score_param.isdigit() else None

        data = get_room_applicants_cv_scores(
            room=room,
            search_query=search_query,
            min_score=min_score,
            request=request
        )
        serializer = RoomCvScoresResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='applicant-cv-scores')
    def applicant_cv_scores(self, request, pk=None):
        """
        Alias for cv-scores endpoint (US-10-T2).
        """
        return self.cv_scores(request, pk=pk)

    @action(detail=True, methods=['get'], url_path=r'cv-scores/(?P<application_id>\d+)')
    def applicant_cv_score_detail(self, request, pk=None, application_id=None):
        """
        US-10-T4: Detailed CV score and skill breakdown for a single applicant in this room.
        """
        room = self.get_object()
        try:
            application = CandidateApplication.objects.select_related('candidate', 'cv').get(
                id=application_id,
                room=room
            )
        except CandidateApplication.DoesNotExist:
            return Response(
                {"error": "Candidate application not found in this room."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = get_applicant_cv_score_data(room, application, request=request)
        serializer = ApplicantCvScoreSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='calculate-scores')
    def calculate_scores(self, request, pk=None):
        """
        US-23-T5: Batch recalculate Final Applicant Scores for all candidates in this Room.
        Permissions: Authenticated, Room Owner or Admin.
        POST /api/recruitment/rooms/{id}/calculate-scores/
        """
        room = self.get_object()
        result = calculate_room_applicant_scores(room)
        serializer = CalculateScoresResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='ranked-applicants')
    def ranked_applicants(self, request, pk=None):
        """
        US-24-T2 & US-24-T4 & US-24-T5: Retrieve ranked candidates for this Room.
        Query params:
          - min_score: float
          - max_score: float
          - search: string
          - status: string
          - ordering: string (default '-final_score')
          - include_unranked: bool (default True)
        """
        room = self.get_object()
        min_score_param = request.query_params.get('min_score')
        max_score_param = request.query_params.get('max_score')
        search = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        ordering = request.query_params.get('ordering', '-final_score')
        include_unranked_param = request.query_params.get('include_unranked', 'true')
        include_unranked = include_unranked_param.lower() not in ['false', '0', 'no']

        min_score = float(min_score_param) if min_score_param and min_score_param.replace('.', '', 1).isdigit() else None
        max_score = float(max_score_param) if max_score_param and max_score_param.replace('.', '', 1).isdigit() else None

        data = get_ranked_room_applicants(
            room_or_id=room,
            min_score=min_score,
            max_score=max_score,
            search=search,
            status_filter=status_filter,
            ordering=ordering,
            include_unranked=include_unranked,
        )
        serializer = RankedApplicantsResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'put', 'patch'], url_path='shortlist-criteria')
    def shortlist_criteria(self, request, pk=None):
        """
        US-25-T2: Configure and view automatic shortlisting criteria for this Room.
        GET: Returns current criteria and evaluated shortlist statistics.
        PUT / PATCH: Validates criteria (min score, top N, combined), persists changes,
        and automatically re-evaluates all applicants in the room.
        """
        room = self.get_object()

        if request.method == 'GET':
            criteria_serializer = RoomShortlistCriteriaSerializer(room)
            eval_data = evaluate_room_shortlist(room, persist=False)
            return Response(
                {
                    "room_id": room.id,
                    "title": room.title,
                    "company_name": room.company_name,
                    "criteria": criteria_serializer.data,
                    "shortlisted_count": eval_data["shortlisted_count"],
                    "total_applicants": eval_data["total_applicants"],
                },
                status=status.HTTP_200_OK
            )

        partial = (request.method == 'PATCH')
        serializer = RoomShortlistCriteriaSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_room = serializer.save()

        # US-25 AC#5: Automatically recalculate shortlist when criteria change
        eval_data = evaluate_room_shortlist(updated_room, persist=True)

        return Response(
            {
                "message": "Shortlisting criteria configured successfully and applicants evaluated.",
                "criteria": serializer.data,
                "shortlist_summary": {
                    "strategy": updated_room.shortlist_strategy,
                    "min_score": updated_room.shortlist_min_score,
                    "top_n": updated_room.shortlist_top_n,
                    "total_applicants": eval_data["total_applicants"],
                    "shortlisted_count": eval_data["shortlisted_count"],
                    "non_shortlisted_count": eval_data["non_shortlisted_count"],
                },
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='shortlist-evaluate')
    def shortlist_evaluate(self, request, pk=None):
        """
        US-25-T3: Explicitly trigger automatic candidate shortlisting re-evaluation.
        POST /api/recruitment/rooms/{id}/shortlist-evaluate/
        """
        room = self.get_object()
        eval_data = evaluate_room_shortlist(room, persist=True)
        serializer = RoomShortlistResponseSerializer(eval_data)
        return Response(
            {
                "message": f"Successfully evaluated shortlisting for {eval_data['total_applicants']} applicants.",
                "evaluation": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='shortlisted-applicants')
    def shortlisted_applicants(self, request, pk=None):
        """
        US-25-T4: Retrieve shortlisted applicants and complete shortlist results for this Room.
        GET /api/recruitment/rooms/{id}/shortlisted-applicants/
        Query params:
          - include_all: bool (default True, includes non-shortlisted candidates with explanation reasons)
        """
        room = self.get_object()
        eval_data = evaluate_room_shortlist(room, persist=False)
        serializer = RoomShortlistResponseSerializer(eval_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='compare-applicants')
    def compare_applicants(self, request, pk=None):
        """
        US-28-T2: Side-by-side applicant comparison endpoint.
        Compares 2 to 4 applicants within this recruitment room,
        highlighting score differentials, skills matches, and behavioral metrics.
        POST /api/recruitment/rooms/{id}/compare-applicants/
        Payload: {"application_ids": [101, 102, 105]}
        """
        room = self.get_object()
        serializer = ApplicantComparisonRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application_ids = serializer.validated_data['application_ids']

        data = compare_room_applicants(
            room=room,
            application_ids=application_ids,
            request_user=request.user,
            request=request
        )
        response_serializer = ApplicantComparisonResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)



class PublicApplicationView(APIView):
    """
    US-21-T3: Public Unauthenticated Endpoint for Candidate Application Link Resolution.
    GET /api/recruitment/apply/{token}/
    
    Verifies token validity, expiration, and active status.
    Returns opening details, requirements, and score weighting if active.
    Returns HTTP 410 Gone if deactivated or expired.
    Returns HTTP 404 Not Found if token does not exist.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        is_valid, room, error_message, status_code = validate_share_token(token)

        if not is_valid:
            if status_code == 404:
                error_code = "LINK_NOT_FOUND"
            elif room and room.status == 'CLOSED':
                error_code = "ROOM_CLOSED"
            elif room and is_token_expired(room):
                error_code = "LINK_EXPIRED"
            else:
                error_code = "LINK_DEACTIVATED"
            return Response(
                {
                    "error": error_message,
                    "code": error_code,
                    "is_active": False,
                    "room_title": room.title if room else None,
                    "company_name": room.company_name if room else None,
                },
                status=status_code
            )

        serializer = PublicRoomDetailsSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicApplicationSubmitView(APIView):
    """
    US-22: Candidate Submission Flow (CV & Video ingestion)
    POST /api/recruitment/apply/{token}/submit/
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, token):
        is_valid, room, error_message, status_code = validate_share_token(token)
        if not is_valid:
            return Response({"error": error_message}, status=status_code)

        full_name = request.data.get('full_name')
        email = request.data.get('email')
        cv_file = request.FILES.get('cv_file')
        video_file = request.FILES.get('video_file')

        if not all([full_name, email, cv_file, video_file]):
            return Response({"error": "Full name, email, CV file, and video file are all required."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Get or create candidate user
        candidate, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'full_name': full_name,
                'role': 'STUDENT',
            }
        )
        if created:
            candidate.set_unusable_password()
            candidate.save()
        elif full_name and candidate.full_name != full_name:
            candidate.full_name = full_name
            candidate.save(update_fields=['full_name'])

        # Check if already applied
        if CandidateApplication.objects.filter(room=room, candidate=candidate).exists():
            return Response({"error": "You have already submitted an application for this role."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Ingest CV
        cv_ext = cv_file.name.split('.')[-1].lower() if '.' in cv_file.name else 'pdf'
        candidate_cv = CandidateCV.objects.create(
            user=candidate,
            file=cv_file,
            original_filename=cv_file.name,
            file_size=cv_file.size,
            file_type=cv_ext
        )

        # Trigger CV Pipeline
        extraction = default_pipeline.process_candidate_cv(candidate_cv)
        if extraction.success:
            ParsedCV.objects.create(
                cv=candidate_cv,
                raw_text=extraction.raw_text,
                skills=extraction.skills,
                education=extraction.education,
                experience=extraction.experience
            )

        # 3. Ingest Video
        vid_ext = video_file.name.split('.')[-1].lower() if '.' in video_file.name else 'mp4'
        video = PresentationVideo.objects.create(
            user=candidate,
            file=video_file,
            original_filename=video_file.name,
            raw_file_size=video_file.size,
            compressed_file_size=video_file.size,
            file_type=vid_ext,
            status='READY_FOR_ANALYSIS'
        )

        # Trigger Presentation Pipeline (synchronous execution, although normally async)
        # We start it to trigger the analysis as per "triggering pipeline"
        PipelineManager.run_pipeline(video)

        # 4. Create Application record
        application = CandidateApplication.objects.create(
            room=room,
            candidate=candidate,
            cv=candidate_cv,
            video=video,
            status='COMPLETED' # Could be PENDING if async
        )

        # US-23: Calculate initial weighted Applicant Score
        try:
            calculate_application_score(application, persist=True)
        except Exception:
            pass

        return Response(
            {
                "message": "Application submitted successfully.",
                "application_id": application.id
            },
            status=status.HTTP_201_CREATED
        )


# ============================================================================
# US-26: HR Candidate Review of AI Results & Human Decision APIs
# ============================================================================

class CandidateApplicationReviewDetailView(APIView):
    """
    US-26-T2: Retrieve granular review details for an applicant including
    candidate metadata, CV breakdown, video metrics, advisory AI recommendation,
    and current HR decision state.
    GET /api/recruitment/applications/<application_id>/review/
    """
    permission_classes = [permissions.IsAuthenticated, IsHRManager, IsApplicationRoomOwner]

    def get(self, request, application_id):
        from django.shortcuts import get_object_or_404
        application = get_object_or_404(
            CandidateApplication.objects.select_related('room', 'candidate', 'cv', 'video', 'hr_decided_by'),
            id=application_id
        )
        self.check_object_permissions(request, application)

        data = get_candidate_review_data(application, request_user=request.user, request=request)
        serializer = CandidateReviewDetailSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CandidateApplicationDecisionView(APIView):
    """
    US-26-T3 & US-26-T5: Record human HR Manager hiring decision on a candidate application.
    Supports CONFIRMED, OVERRIDDEN, REJECTED, and ON_HOLD.
    Enforces mandatory justification note if overriding the AI recommendation.
    POST /api/recruitment/applications/<application_id>/decision/
    GET  /api/recruitment/applications/<application_id>/decision/
    """
    permission_classes = [permissions.IsAuthenticated, IsHRManager, IsApplicationRoomOwner]

    def get_object(self, application_id):
        from django.shortcuts import get_object_or_404
        application = get_object_or_404(
            CandidateApplication.objects.select_related('room', 'candidate', 'cv', 'video', 'hr_decided_by'),
            id=application_id
        )
        self.check_object_permissions(self.request, application)
        return application

    def get(self, request, application_id):
        application = self.get_object(application_id)
        data = get_candidate_review_data(application, request_user=request.user, request=request)
        serializer = CandidateReviewDetailSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, application_id):
        application = self.get_object(application_id)

        serializer = CandidateDecisionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        decision = serializer.validated_data['decision']
        notes = serializer.validated_data.get('notes', '')

        result = record_candidate_review_decision(
            application=application,
            decision=decision,
            notes=notes,
            request_user=request.user
        )

        response_serializer = CandidateDecisionResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# US-27: Explainable Applicant Score Breakdown & Transparency
# ============================================================================

class ApplicantScoreBreakdownView(APIView):
    """
    US-27-T2: Explainable score breakdown endpoint.
    Retrieves component weights, raw scores, points contribution, mathematical formula,
    and missing component handling for an applicant.
    GET /api/recruitment/applications/<application_id>/score-breakdown/
    """
    permission_classes = [permissions.IsAuthenticated, IsHRManager, IsApplicationRoomOwner]

    def get(self, request, application_id=None, pk=None):
        from django.shortcuts import get_object_or_404
        app_id = application_id or pk
        application = get_object_or_404(
            CandidateApplication.objects.select_related('room', 'candidate', 'cv', 'video'),
            id=app_id
        )
        self.check_object_permissions(request, application)

        breakdown_data = get_applicant_score_breakdown(application, request_user=request.user, request=request)
        serializer = ApplicantScoreBreakdownSerializer(breakdown_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# US-29: Manage Multiple Client Companies ViewSet
# ============================================================================

class ClientCompanyViewSet(viewsets.ModelViewSet):
    """
    US-29-T2 & US-29-T3: Agency Administrator Client Company Management.
    Provides complete CRUD, soft deactivation/reactivation, multi-tenant isolation,
    and dashboard KPI metrics. Only accessible to users with the AGENCY_ADMIN role.
    """
    serializer_class = ClientCompanySerializer
    permission_classes = [permissions.IsAuthenticated, IsAgencyAdmin, IsClientAgencyOwner]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return ClientCompany.objects.none()

        qs = ClientCompany.objects.filter(agency=user).prefetch_related('rooms').order_by('-created_at')

        # Optional query filters
        search_query = self.request.query_params.get('q', '').strip()
        if search_query:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=search_query) |
                Q(industry__icontains=search_query) |
                Q(contact_person__icontains=search_query) |
                Q(contact_email__icontains=search_query)
            )

        industry = self.request.query_params.get('industry', '').strip()
        if industry and industry.lower() != 'all':
            qs = qs.filter(industry__iexact=industry)

        status_param = self.request.query_params.get('status', '').strip().lower()
        if status_param == 'active':
            qs = qs.filter(is_active=True)
        elif status_param == 'deactivated':
            qs = qs.filter(is_active=False)

        return qs

    def perform_create(self, serializer):
        serializer.save(agency=self.request.user)

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """
        US-29-T5: Toggle client company operational status between active and deactivated.
        """
        company = self.get_object()
        company.is_active = not company.is_active
        company.save(update_fields=['is_active', 'updated_at'])
        action_verb = "activated" if company.is_active else "deactivated"
        return Response({
            "message": f"Client company '{company.name}' successfully {action_verb}.",
            "is_active": company.is_active,
            "client": ClientCompanySerializer(company, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='summary-stats')
    def summary_stats(self, request):
        """
        US-29-T4: Return high-level KPI metrics for the agency dashboard.
        """
        user_clients = ClientCompany.objects.filter(agency=request.user)
        total_clients = user_clients.count()
        active_clients = user_clients.filter(is_active=True).count()
        deactivated_clients = total_clients - active_clients
        associated_rooms = RecruitmentRoom.objects.filter(client_company__agency=request.user).count()

        data = {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "deactivated_clients": deactivated_clients,
            "associated_rooms": associated_rooms,
        }
        return Response(data, status=status.HTTP_200_OK)




