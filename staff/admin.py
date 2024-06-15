from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe, SafeString
from django.utils.translation import gettext_lazy as _

from common.admin import BaseAdmin
from staff.models import Employee, DutyRoster


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    """Admin interface for Employees"""

    save_on_top = True
    list_display = (
        "display_thumbnail",
        "username",
        "first_name",
        "last_name",
        "job_title",
        "phone",
        "can_duty",
        "is_active",
    )
    list_display_links = ("username", "display_thumbnail")
    list_editable = (
        "is_active",
        "can_duty",
    )
    list_filter = UserAdmin.list_filter + (
        "job_title",
        "can_duty",
    )
    readonly_fields = UserAdmin.readonly_fields + ("display_thumbnail",)
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] += (
        "date_of_birth",
        "job_title",
        "phone",
        "telegram_id",
        "photo",
        "can_duty",
        "display_thumbnail",
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "job_title",
                    "date_of_birth",
                    "phone",
                    "telegram_id",
                    "can_duty",
                    "photo",
                    "display_thumbnail",
                    "is_active",
                )
            },
        ),
    )

    def display_thumbnail(self, obj: Employee) -> SafeString:
        """View image for admin"""
        default_photo_path = (
            settings.MEDIA_URL + "staff_photos/no_photo/no_photo.png"
        )
        if obj.photo:
            return mark_safe(
                f"<img src='{obj.photo.url}' width='40' height='40'>"
            )
        return mark_safe(
            f"<img src='{default_photo_path}' width='40' height='40'>"
        )

    display_thumbnail.short_description = _("Avatar")


@admin.register(DutyRoster)
class DutyRosterAdmin(BaseAdmin):
    list_display = ("employee", "start_date", "end_date")
    search_fields = ("start_date", "end_date")
    list_filter = ("employee",)
    fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "employee",
                    "start_date",
                    "end_date",
                )
            },
        ),
    ) + BaseAdmin.fieldsets
