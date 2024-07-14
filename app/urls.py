from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    # path(
    #     "accounts/profile/",
    #     TemplateView.as_view(template_name="staff/employee_detail.html"),
    #     name="account_profile",
    # ),
    path("", include("vacation.urls")),
    path("", include("staff.urls")),
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    # Serve media files
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
