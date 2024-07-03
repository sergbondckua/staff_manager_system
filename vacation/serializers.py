from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.enums import StatusRequestChoices
from vacation.models import LeaveRequest, VacationUsed, LeaveType


class VacationLeaveTypeSerializer(serializers.ModelSerializer):

    title = serializers.SerializerMethodField()

    @staticmethod
    def get_title(obj):
        represent = (
            obj.title if obj.parent is None else f"{obj.parent} ({obj.title})"
        )
        return str(represent)

    class Meta:
        model = LeaveType
        fields = ("id", "title")


class LeaveRequestUserSerializer(serializers.ModelSerializer):
    """Leave request serializer class"""

    expired = serializers.BooleanField(default=False, read_only=True)
    number_of_days = serializers.IntegerField(read_only=True)
    employee = serializers.StringRelatedField()
    # leave_type = serializers.StringRelatedField()
    status = serializers.ChoiceField(
        choices=StatusRequestChoices,
        read_only=True,
        default=StatusRequestChoices.PENDING,
    )
    auth_date = serializers.CharField(read_only=True, required=False)
    hash = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = LeaveRequest
        exclude = ("created_at", "updated_at")

    def validate(self, data):
        request = self.context.get("request")
        employee = request.user

        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not employee:
            raise ValidationError(_("Employee must be set"))

        # Check for overlapping leave requests for the employee
        if start_date and end_date:
            overlapping_requests = LeaveRequest.objects.filter(
                employee=employee,
                start_date__lte=end_date,
                end_date__gte=start_date,
            )

            # If we are updating an instance, exclude the current instance from the check
            if self.instance and self.instance.pk:
                overlapping_requests = overlapping_requests.exclude(
                    pk=self.instance.pk
                )

            if overlapping_requests.exists():
                overlapping_dates = ", ".join(
                    f"{req.start_date} - {req.end_date}"
                    for req in overlapping_requests
                )
                raise ValidationError(
                    _(
                        f"There is an overlap with other leave requests for the selected dates: {overlapping_dates}.",
                    )
                )

        return data


class VacationUsedSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacationUsed
        fields = "__all__"
