from django import forms
from django.utils import timezone

from common.enums import UKRAINIAN_MONTHS
from .models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    """Form for creating vacation requests."""

    class Meta:
        model = LeaveRequest
        fields = [
            "reason",
            "start_date",
            "end_date",
        ]
        widgets = {
            "start_date": forms.SelectDateWidget(
                years=range(timezone.now().year, timezone.now().year + 1),
                months={
                    i: UKRAINIAN_MONTHS[i]
                    for i in range(timezone.now().month, 13)
                },
                attrs={"required": "True"},
            ),
            "end_date": forms.SelectDateWidget(
                years=range(timezone.now().year, timezone.now().year + 1),
                months={
                    i: UKRAINIAN_MONTHS[i]
                    for i in range(timezone.now().month, 13)
                },
                attrs={"required": "True"},
            ),
        }
