import os
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import BaseModel
from staff.services import generate_path


class Employee(AbstractUser):
    """Custom staff user model."""

    job_title = models.CharField(verbose_name=_("Job Title"), max_length=50)
    date_of_birth = models.DateField(
        verbose_name=_("Date of birth"),
        blank=True,
        null=True,
    )
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,13}$",
        message=_(
            "Phone number must be in the format: '+380999999'. Up to 13 digits allowed."
        ),
    )
    phone = models.CharField(
        verbose_name=_("Phone number"),
        validators=[phone_regex],
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        help_text="Phone number must be in the format: '+380999999'. Up to 13 digits allowed.",
    )
    telegram_id = models.PositiveBigIntegerField(
        verbose_name=_("Telegram id"),
        unique=True,
        blank=True,
        null=True,
    )
    can_duty = models.BooleanField(
        verbose_name=_("Can Duty"),
        default=False,
        help_text=_(
            "Indicates whether the employee is eligible for weekend duty."
        ),
    )
    photo = models.ImageField(
        verbose_name=_("Photo"),
        blank=True,
        null=True,
        default="staff_photos/no_photo/no_photo.png",
        upload_to=generate_path,
        help_text=_("Upload image: (PNG, JPEG, JPG)"),
    )

    def __str__(self) -> str:
        """Return string representation of the Employee."""
        return (
            f"{self.first_name} {self.last_name}"
            if self.first_name and self.last_name is not None
            else f"{self.username}"
        )

    def delete(self, *args, **kwargs):
        """Delete the Employee and its associated photo directory."""
        if self.photo:
            photo_path = self.photo.path
            if os.path.exists(photo_path):
                # Delete the directory containing the photo
                shutil.rmtree(os.path.dirname(photo_path))
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ("username",)
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")


class DutyRoster(BaseModel):
    """Model to store the duty roster for employees."""

    employee = models.ForeignKey(
        "Employee", on_delete=models.CASCADE, related_name="duty_rosters"
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))

    def __str__(self):
        return (
            f"{self.employee} ({self.start_date.strftime('%A, %d.%m.%Y')} - "
            f"{self.end_date.strftime('%A, %d.%m.%Y')})"
        )

    class Meta:
        verbose_name = _("Duty Roster")
        verbose_name_plural = _("Duty Rosters")
        ordering = ("-start_date",)
