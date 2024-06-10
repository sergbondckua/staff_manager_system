from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.enums import UKRAINIAN_MONTHS
from .models import LeaveRequest, LeaveType


class LeaveTypeChoiceField(forms.ModelChoiceField):
    """The type of choice field for Leave requests."""

    def label_from_instance(self, obj):
        level = 0
        parent = obj.parent
        while parent:
            level += 1
            parent = parent.parent

        return (
            str(obj.title)
            if obj.parent is None
            else f"{obj.parent} {'—' * level}> {obj.title}"
        )

    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, queryset=queryset, **kwargs)

        # If a queryset is provided, filter it to exclude objects with
        # subtypes if the queryset supports filtering
        if queryset is not None:
            self.queryset = (
                queryset.filter(subtypes__isnull=True)
                if hasattr(queryset, "filter")
                else queryset
            )


class LeaveRequestForm(forms.ModelForm):
    """Form for creating vacation requests."""

    leave_type = LeaveTypeChoiceField(
        queryset=LeaveType.objects.all(),
        required=True,
        widget=forms.Select,
        label=_("Reason"),
    )

    class Meta:
        model = LeaveRequest
        fields = [
            "leave_type",
            "start_date",
            "end_date",
            "comment",
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
            "comment": forms.Textarea(attrs={"rows": "5", "cols": "33"})
        }
