from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.enums import ReasonRequestChoices, StatusRequestChoices
from common.models import BaseModel
from staff.models import Employee


class VacationUsed(BaseModel):
    """Counting vacation days used."""

    employee = models.ForeignKey(
        Employee,
        verbose_name=_("Employee"),
        related_name="vacation_days",
        on_delete=models.CASCADE,
    )
    days = models.PositiveSmallIntegerField(
        verbose_name=_("Days used"),
        default=0,
    )

    def __str__(self):
        return (
            f"{self.employee.first_name} {self.employee.last_name}: "
            f"{self.days} {_('days')}"
        )

    class Meta:
        ordering = ("days",)
        verbose_name = _("Vacation used by day")
        verbose_name_plural = _("Vacation used by days")


class LeaveRequest(BaseModel):
    """Model for leave requests."""

    employee = models.ForeignKey(
        Employee,
        verbose_name=_("Employee"),
        related_name="leave_requests",
        on_delete=models.CASCADE,
    )
    reason = models.CharField(
        verbose_name=_("Reason"),
        max_length=100,
        default=ReasonRequestChoices.VACATION,
        choices=ReasonRequestChoices.choices,
    )
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    number_of_days = models.PositiveSmallIntegerField(
        verbose_name=_("Number of days"),
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=20,
        default=StatusRequestChoices.PENDING,
        choices=StatusRequestChoices.choices,
    )

    def clean(self):
        """
        Model validation method.
        Ensures the end date is not earlier than the start date.
        """
        if self.end_date < self.start_date:
            raise ValidationError(
                _("End date cannot be earlier than start date")
            )

    def calculate_number_of_days(self):
        """Calculates the number of days."""
        self.number_of_days = (self.end_date - self.start_date).days

    def get_change_status(self):
        """Changes the status of request."""
        if self.status == StatusRequestChoices.APPROVED:
            vacation_record, _ = VacationUsed.objects.get_or_create(
                employee=self.employee
            )
            vacation_record.days += self.number_of_days
            vacation_record.save()

    def save(self, *args, **kwargs):
        """Overrides the save method."""
        self.clean()
        self.calculate_number_of_days()
        super().save(*args, **kwargs)
        self.get_change_status()

    def __str__(self):
        return f"{self.employee}: {self.reason}-{self.number_of_days} day(s)"

    class Meta:
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")
