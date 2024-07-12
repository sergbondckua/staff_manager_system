from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.enums import UKRAINIAN_MONTHS
from .models import LeaveRequest, LeaveType


class LeaveTypeChoiceField(forms.ModelChoiceField):
    """Custom choice field for LeaveType model that includes hierarchy in the label."""

    def label_from_instance(self, obj) -> str:
        """Generate a label for the instance that includes its hierarchy."""
        level = 0
        parent = obj.parent
        while parent:
            level += 1
            parent = parent.parent

        # Construct the label showing the hierarchy with '—' characters
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
    """Form for creating and validating leave requests."""

    leave_type = LeaveTypeChoiceField(
        queryset=LeaveType.objects.all(),
        required=True,
        widget=forms.Select(
            attrs={"class": "form-control js-example-basic-single w-100"}
        ),
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
                attrs={"required": "True", "class": "form-control"},
            ),
            "end_date": forms.SelectDateWidget(
                years=range(timezone.now().year, timezone.now().year + 1),
                months={
                    i: UKRAINIAN_MONTHS[i]
                    for i in range(timezone.now().month, 13)
                },
                attrs={"required": "True", "class": "form-control"},
            ),
            "comment": forms.Textarea(
                attrs={"rows": "5", "cols": "33", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Ensure the employee is set
        if not self.employee:
            raise forms.ValidationError(_("Employee must be set"))

        # Validate that end date is not before start date
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError(
                    _("End date cannot be earlier than start date")
                )
            # Validate that start date is not in the past
            elif start_date < timezone.now().date():
                raise forms.ValidationError(
                    _("Start date cannot be later than current date")
                )
            # Check for overlapping leave requests for the employee
            overlapping_requests = LeaveRequest.objects.filter(
                employee=self.employee,
                start_date__lt=end_date,
                end_date__gt=start_date,
            ).exclude(pk=self.instance.pk)

            if overlapping_requests.exists():
                overlapping_dates = ", ".join(
                    f"{req.start_date} - {req.end_date}"
                    for req in overlapping_requests
                )
                raise forms.ValidationError(
                    _(
                        f"There is an overlap with other leave requests for the selected dates: {overlapping_dates}.",
                    )
                )
        return cleaned_data
