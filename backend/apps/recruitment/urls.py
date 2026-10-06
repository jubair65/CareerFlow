from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecruitmentRoomViewSet

app_name = 'recruitment'

router = DefaultRouter()
router.register(r'rooms', RecruitmentRoomViewSet, basename='room')

urlpatterns = [
    path('', include(router.urls)),
]
