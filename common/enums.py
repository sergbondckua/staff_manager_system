from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusRequestChoices(models.TextChoices):
    """The choices for the status."""

    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


UKRAINIAN_MONTHS = {
    1: "Січень",
    2: "Лютий",
    3: "Березень",
    4: "Квітень",
    5: "Травень",
    6: "Червень",
    7: "Липень",
    8: "Серпень",
    9: "Вересень",
    10: "Жовтень",
    11: "Листопад",
    12: "Грудень",
}
