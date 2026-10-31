from django.urls import path
from .views import (
    PresentationVideoDetailView,
    PracticeSessionRenameView,
)

app_name = 'practice'

urlpatterns = [
    path('<int:pk>/', PresentationVideoDetailView.as_view(), name='practice_detail'),
    path('<int:pk>/rename/', PracticeSessionRenameView.as_view(), name='practice_rename'),
]
