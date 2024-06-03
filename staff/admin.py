from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from staff.models import Employee


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    """Admin interface for Employees"""

    list_display = UserAdmin.list_display + (
        "job_title",
        "date_of_birth",
        "phone",
        "photo",
        "is_active",
    )
    list_filter = UserAdmin.list_filter + (
        "job_title",
        "is_active",
    )
