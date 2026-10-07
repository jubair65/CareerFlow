from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruitmentRoomViewSet, PublicApplicationView, PublicApplicationSubmitView

app_name = 'recruitment'

router = DefaultRouter()
router.register(r'rooms', RecruitmentRoomViewSet, basename='room')

urlpatterns = [
    path('apply/<str:token>/submit/', PublicApplicationSubmitView.as_view(), name='public-apply-submit'),
    path('apply/<str:token>/', PublicApplicationView.as_view(), name='public-apply'),
    path('', include(router.urls)),
]

