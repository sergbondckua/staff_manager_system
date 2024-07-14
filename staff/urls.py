from django.urls import path
from . import views

urlpatterns = [
    path(
        "accounts/profile/",
        views.ProfileView.as_view(),
        name="account_profile",
    ),
    path(
        "accounts/profile/edit/",
        views.ProfileUpdateView.as_view(),
        name="account_profile_update",
    ),
]

app_name = "staff"
