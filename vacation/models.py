import asyncio

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from common.enums import StatusRequestChoices
from common.models import BaseModel
from staff.models import Employee
from telegram.bot import bot


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

    def clean(self):
        """
        Model validation method.
        Ensures the end date is not earlier than the start date.
        """
        if self.end_date <= self.start_date:
            raise ValidationError(
                _("End date cannot be earlier than start date")
            )
        elif self.start_date < timezone.now().date():
            raise ValidationError(
                _("Start date cannot be later than current date")
            )

    def calculate_number_of_days(self):
        """Calculates the number of days."""
        self.number_of_days = (self.end_date - self.start_date).days

    def submit_for_approval(self):
        # TODO: Логіка для відправки на погодження
        self.status = StatusRequestChoices.PENDING
        self.save()
        asyncio.run(
            bot.send_message(
                chat_id=541696726,
                text=f"<b>Approval request #{self.pk}:</b>\n{self.employee}\n"
                f"{self.start_date.strftime('%d %B %Y')} - "
                f"{self.end_date.strftime('%d %B %Y')} - {self.number_of_days} дні(в)",
            )
        )

    def save(self, *args, **kwargs):
        """Overrides the save method."""
        self.clean()
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
