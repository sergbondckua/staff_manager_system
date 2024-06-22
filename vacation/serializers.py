from rest_framework import serializers

from common.enums import StatusRequestChoices
from vacation.models import LeaveRequest, VacationUsed, LeaveType


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

    class Meta:
        model = LeaveRequest
        exclude = ("created_at", "updated_at")


class VacationUsedSerializer(serializers.ModelSerializer):
    class Meta:
        model = VacationUsed
        fields = "__all__"
