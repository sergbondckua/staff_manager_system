from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from common.admin import BaseAdmin
from vacation.models import LeaveRequest, VacationUsed, LeaveType


@admin.register(VacationUsed)
class VacationUsedAdmin(BaseAdmin):
    """This admin is used to manage the installation of Vacation"""

    list_display = (
        "employee",
        "days",
    )
    list_filter = ("employee", "days")
    search_fields = ("employee",)
    save_on_top = True
    save_as = True
    fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "employee",
                    "days",
                )
            },
        ),
    ) + BaseAdmin.fieldsets


@admin.register(LeaveRequest)
class LeaveRequestAdmin(BaseAdmin):
    """Admin interface for leave requests."""

    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "number_of_days",
        "status",
    )
    list_display_links = ("employee",)
    list_filter = ("employee", "status", "start_date", "end_date")
    list_editable = ("status",)
    search_fields = ("employee",)
    save_on_top = True
    save_as = True
    fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "employee",
                    "leave_type",
                    ("start_date", "end_date"),
                    "status",
                )
            },
        ),
    ) + BaseAdmin.fieldsets

    add_fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "employee",
                    "leave_type",
                    ("start_date", "end_date", "number_of_days"),
                    "status",
                )
            },
        ),
    ) + BaseAdmin.fieldsets


@admin.register(LeaveType)
class LeaveTypeAdmin(BaseAdmin):
    """Admin interface for Leave Type."""

    list_display = (
        "title",
        "parent",
    )
    list_display_links = ("title",)
    list_filter = ("parent",)
    search_fields = ("title",)
    save_on_top = True
    save_as = True
    fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "title",
                    "parent",
                )
            },
        ),
    ) + BaseAdmin.fieldsets

    add_fieldsets = (
        (
            _("Information"),
            {
                "fields": (
                    "title",
                    "parent",
                )
            },
        ),
    ) + BaseAdmin.fieldsets
