from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from common.enums import StatusRequestChoices
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
        if self.end_date <= self.start_date:
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
        return (
            f"{self.employee}: {self.leave_type}-{self.number_of_days} day(s)"
        )

    class Meta:
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")


class LeaveType(BaseModel):
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
        return str(self.title) if self.parent is None else f"{self.parent} -> {self.title}"

    def get_subtype(self):
        return self.subtypes.all()


@receiver(post_migrate)
def create_default_leave_type(sender, **kwargs):
    if (
            sender.name == "vacation"
    ):  # Creating leave type for 'vacation'
        annual, _ = LeaveType.objects.get_or_create(
            title="Annual", parent=None
        )
        sick, _ = LeaveType.objects.get_or_create(
            title="Sick", parent=None
        )
        LeaveType.objects.get_or_create(title="Home", parent=sick)
        LeaveType.objects.get_or_create(title="Hospital", parent=sick)
