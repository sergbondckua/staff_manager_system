from django import forms

from staff.models import Employee


class EmployeeForm(forms.ModelForm):
    """Employees form class"""

    class Meta:
        model = Employee
        fields = (
            "first_name",
            "last_name",
            "email",
            "job_title",
            "date_of_birth",
            "phone",
            "telegram_id",
            "photo",
        )
