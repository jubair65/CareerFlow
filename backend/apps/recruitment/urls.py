from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecruitmentRoomViewSet,
    PublicApplicationView,
    PublicApplicationSubmitView,
    CandidateApplicationDecisionView,
    CandidateApplicationReviewDetailView,
    ApplicantScoreBreakdownView,
    ClientCompanyViewSet,
    AgencyRoomViewSet,
    AgencyCrossClientApplicantViewSet,
    AgencyForwardShortlistView,
    AgencyForwardHistoryView,
    CandidateApplicationReportPdfView,
    RecruitmentRoomSummaryPdfView,
    RecruitmentRoomExportCsvView,
    RecruitmentRoomExportExcelView,
    ApplicantStatusListView,
    ApplicantStatusDetailView,
    CandidateMyApplicationsListView,
    CandidateMyApplicationDetailView,
    PublicJobRoomsListView,
    PublicJobRoomDetailView,
    ApplicationSubmissionGatekeeperView,
)

app_name = 'recruitment'

router = DefaultRouter()
router.register(r'rooms', RecruitmentRoomViewSet, basename='room')
router.register(r'agency/clients', ClientCompanyViewSet, basename='agency-clients')
router.register(r'agency/rooms', AgencyRoomViewSet, basename='agency-rooms')
router.register(r'agency/applicants', AgencyCrossClientApplicantViewSet, basename='agency-applicants')

urlpatterns = [
    # US-46: Bulk Applicant Data Export (CSV / Excel) Endpoints
    path('rooms/<int:room_id>/export/csv/', RecruitmentRoomExportCsvView.as_view(), name='room-export-csv'),
    path('rooms/<int:room_id>/export/excel/', RecruitmentRoomExportExcelView.as_view(), name='room-export-excel'),

    # US-43B: Applicant Job Room Discovery Dashboard (Job Board) Endpoints
    path('rooms/public/', PublicJobRoomsListView.as_view(), name='public-job-rooms-list'),
    path('rooms/public/<int:room_id>/', PublicJobRoomDetailView.as_view(), name='public-job-room-detail'),

    # US-45-T3: Room Status & Deadline Application Submission Gatekeeper
    path('applications/submit/', ApplicationSubmissionGatekeeperView.as_view(), name='application-submit-gatekeeper'),

    # US-43: Candidate "My Applications" Tracking Dashboard Endpoints
    path('applications/my/', CandidateMyApplicationsListView.as_view(), name='candidate-my-applications-list'),
    path('applications/my/<int:application_id>/', CandidateMyApplicationDetailView.as_view(), name='candidate-my-application-detail'),

    # US-35: Applicant Application Status & Stage Milestones Endpoints
    path('applications/my-status/', ApplicantStatusListView.as_view(), name='applicant-status-list'),
    path('applications/<int:application_id>/status/', ApplicantStatusDetailView.as_view(), name='applicant-status-detail'),

    # US-33: Downloadable Candidate & Room PDF Reports Endpoints
    path('applications/<int:application_id>/report-pdf/', CandidateApplicationReportPdfView.as_view(), name='application-report-pdf'),
    path('rooms/<int:room_id>/summary-pdf/', RecruitmentRoomSummaryPdfView.as_view(), name='room-summary-pdf'),

    # US-32: Agency Shortlist Forwarding to Client Endpoints
    path('agency/forward-shortlist/', AgencyForwardShortlistView.as_view(), name='agency-forward-shortlist'),
    path('agency/forward-history/', AgencyForwardHistoryView.as_view(), name='agency-forward-history'),

    # US-26: HR Candidate Review & Decision Endpoints
    path('applications/<int:application_id>/decision/', CandidateApplicationDecisionView.as_view(), name='application-decision'),
    path('applications/<int:application_id>/review/', CandidateApplicationReviewDetailView.as_view(), name='application-review-detail'),

    # US-27: Explainable Applicant Score Breakdown & Transparency Endpoint
    path('applications/<int:application_id>/score-breakdown/', ApplicantScoreBreakdownView.as_view(), name='application-score-breakdown'),

    path('apply/<str:token>/submit/', PublicApplicationSubmitView.as_view(), name='public-apply-submit'),
    path('apply/<str:token>/', PublicApplicationView.as_view(), name='public-apply'),
    path('', include(router.urls)),
]
