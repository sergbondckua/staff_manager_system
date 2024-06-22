from django.urls import path, include
from rest_framework.routers import DefaultRouter

from vacation.views import (
    LeaveRequestListView,
    LeaveRequestDetailView,
    LeaveRequestCreateView,
    LeaveRequestUpdateView,
    LeaveRequestDeleteView,
    LeaveRequestUserViewSet,
)

router = DefaultRouter()
router.register(
    r"leave-requests", LeaveRequestUserViewSet, basename="leave-request"
)

urlpatterns = [
    path(
        "leave_requests/",
        LeaveRequestListView.as_view(),
        name="leave_request_list",
    ),
    path(
        "leave_requests/<int:pk>/",
        LeaveRequestDetailView.as_view(),
        name="leave_request_detail",
    ),
    path(
        "leave_requests/new/",
        LeaveRequestCreateView.as_view(),
        name="leave_request_create",
    ),
    path(
        "leave_requests/<int:pk>/edit/",
        LeaveRequestUpdateView.as_view(),
        name="leave_request_update",
    ),
    path(
        "leave_requests/<int:pk>/delete/",
        LeaveRequestDeleteView.as_view(),
        name="leave_request_delete",
    ),
    # API
    path("api/", include(router.urls)),
]

app_name = "vacation"
