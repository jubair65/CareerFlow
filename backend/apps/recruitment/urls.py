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
)

app_name = 'recruitment'

router = DefaultRouter()
router.register(r'rooms', RecruitmentRoomViewSet, basename='room')
router.register(r'agency/clients', ClientCompanyViewSet, basename='agency-clients')
router.register(r'agency/rooms', AgencyRoomViewSet, basename='agency-rooms')
router.register(r'agency/applicants', AgencyCrossClientApplicantViewSet, basename='agency-applicants')

urlpatterns = [
    # US-26: HR Candidate Review & Decision Endpoints
    path('applications/<int:application_id>/decision/', CandidateApplicationDecisionView.as_view(), name='application-decision'),
    path('applications/<int:application_id>/review/', CandidateApplicationReviewDetailView.as_view(), name='application-review-detail'),

    # US-27: Explainable Applicant Score Breakdown & Transparency Endpoint
    path('applications/<int:application_id>/score-breakdown/', ApplicantScoreBreakdownView.as_view(), name='application-score-breakdown'),

    path('apply/<str:token>/submit/', PublicApplicationSubmitView.as_view(), name='public-apply-submit'),
    path('apply/<str:token>/', PublicApplicationView.as_view(), name='public-apply'),
    path('', include(router.urls)),
]


