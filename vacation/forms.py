from django import forms
from .models import LeaveRequest


class LeaveRequestForm(forms.ModelForm):
    """Form for creating vacation requests."""

    class Meta:
        model = LeaveRequest
        fields = [
            "employee",
            "reason",
            "start_date",
            "end_date",
        ]
        widgets = {
            "employee": forms.RadioSelect(
                attrs={
                    "checked": "checked",
                    "required": "True",
                }
            ),
            "start_date": forms.SelectDateWidget(attrs={"required": "True"}),
            "end_date": forms.SelectDateWidget(attrs={"required": "True"}),
        }

    def clean_end_date(self):
        """Ensure the end date is not earlier than the start date."""

        start_date = self.cleaned_data.get("start_date")
        end_date = self.cleaned_data.get("end_date")

        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date")

        return end_date

    def clean(self):
        """Calls the model clean method for additional validation."""

        cleaned_data = super().clean()
        self.instance.start_date = cleaned_data.get("start_date")
        self.instance.end_date = cleaned_data.get("end_date")
        self.instance.clean()
        return cleaned_data
