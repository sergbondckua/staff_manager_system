from django import forms
from django.utils import timezone

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
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
            "job_title": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "date_of_birth": forms.SelectDateWidget(
                years=range(timezone.now().year - 70, timezone.now().year - 18),
                attrs={
                    "style": "width: auto; display: inline-block;",
                    "required": "True",
                    "type": "date",
                    "class": "form-select",
                },
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"},
            ),
            "telegram_id": forms.TextInput(
                attrs={"class": "form-control", "readonly": "True"},
            ),
            "photo": forms.ClearableFileInput(
                attrs={"class": "form-control"},
            ),
        }
