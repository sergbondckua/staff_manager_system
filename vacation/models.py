from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from common.enums import StatusRequestChoices
from common.models import BaseModel
from staff.models import Employee
from vacation.tasks import send_vacation_request_for_approval


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
    leave_type = models.ForeignKey(
        "LeaveType",
        verbose_name=_("Leave Type"),
        on_delete=models.CASCADE,
        related_name="leave_types",
    )
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    number_of_days = models.PositiveSmallIntegerField(
        verbose_name=_("Number of days"),
    )
    comment = models.TextField(
        verbose_name=_("Comment"),
        max_length=255,
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=20,
        default=StatusRequestChoices.SAVED,
        choices=StatusRequestChoices.choices,
    )
    expired = models.BooleanField(
        verbose_name=_("Expired"),
        default=False,
        help_text=_(
            "If 'True', these days are not counted as vacation days used.<br>"
            "It is set automatically by the system at the appointed time."
        ),
    )
    history = HistoricalRecords()

    def calculate_number_of_days(self):
        """Calculates the number of days."""
        self.number_of_days = (self.end_date - self.start_date).days

    def submit_for_approval(self):
        """Submit the leave request for approval."""

        # Format the approval message
        msg = _(
            f"<b>Approval request #{self.pk}:</b>\n{self.employee}\n"
            f"{self.start_date.strftime('%d %B %Y')} - "
            f"{self.end_date.strftime('%d %B %Y')} - {self.number_of_days} day(s) "
            f"{self.leave_type}\n"
            f"<i>{self.comment if self.comment else ''}</i>"
        )

        # Update the status to pending
        self.status = StatusRequestChoices.PENDING
        self.save()

        # [celery] Sends a message to managers requesting approval in Telegram
        send_vacation_request_for_approval.delay(text=msg)

    def save(self, *args, **kwargs):
        """Overrides the save method."""
        self.calculate_number_of_days()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.pk} {self.leave_type}: {self.employee} ({self.number_of_days} day's)"

    class Meta:
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")


class LeaveType(BaseModel):
    """The type of request to leave."""

    title = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Parent"),
        on_delete=models.CASCADE,
        related_name="subtypes",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Leave type")
        verbose_name_plural = _("Leave types")

    def __str__(self):
        return (
            str(self.title)
            if self.parent is None
            else f"{self.parent} - {self.title}"
        )

    def get_subtype(self):
        return self.subtypes.all()
