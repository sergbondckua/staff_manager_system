from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from common.admin import BaseAdmin
from common.enums import StatusRequestChoices
from vacation.models import LeaveRequest, VacationUsed, LeaveType


@admin.register(VacationUsed)
class VacationUsedAdmin(BaseAdmin):
    """This admin is used to manage the installation of Vacation"""

    def has_add_permission(self, request):
        """Disable the ability to add new entries"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable the ability to change"""
        return False

    # def has_delete_permission(self, request, obj=None):
    #     """Disable the ability to delete"""
    #     return False

    list_display = (
        "employee",
        "days",
    )
    list_filter = ("employee",)
    search_fields = ("employee",)
    readonly_fields = ("employee", "days")
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
    )


@admin.register(LeaveRequest)
class LeaveRequestAdmin(BaseAdmin):
    """Admin interface for leave requests."""

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj)
        if obj and obj.status == StatusRequestChoices.APPROVED:
            readonly_fields += ("status",)
        return readonly_fields

    list_display = (
        "employee",
        "leave_type",
        "start_date",
        "number_of_days",
        "status",
    )
    list_display_links = ("employee",)
    list_filter = ("employee", "status", "start_date", "end_date")
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
                    "comment",
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
                    "comment",
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
