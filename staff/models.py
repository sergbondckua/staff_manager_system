from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from staff.service import generate_path


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
    )
    telegram_id = models.PositiveIntegerField(
        verbose_name=_("Telegram id"),
        unique=True,
        blank=True,
        null=True,
    )
    photo = models.ImageField(
        verbose_name=_("Photo"),
        blank=True,
        null=True,
        default=None,
        upload_to=generate_path,
        help_text=_("Upload image: (PNG, JPEG, JPG)"),
    )
    is_active = models.BooleanField(verbose_name=_("Active"), default=True)

    def __str__(self) -> str:
        """Return string representation of the Employee."""
        return (
            f"{self.first_name} {self.last_name}: ({self.job_title})"
            if self.first_name and self.last_name is not None
            else f"{self.username}: ({self.job_title})"
        )

    class Meta:
        ordering = ("username",)
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
