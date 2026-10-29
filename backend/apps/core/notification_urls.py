from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationDetailView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='root_notification_list'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(), name='root_notification_mark_read'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='root_notification_mark_all_read'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='root_notification_detail'),
]

