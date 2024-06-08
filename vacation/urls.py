from django.urls import path
from .views import (
    LeaveRequestListView,
    LeaveRequestDetailView,
    LeaveRequestCreateView,
    LeaveRequestUpdateView,
    LeaveRequestDeleteView,
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
]

app_name = "vacation"
