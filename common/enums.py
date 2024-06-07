from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusRequestChoices(models.TextChoices):
    """The choices for the status."""

    PENDING = "pending", _("Pending")
    APPROVED = "approved", _("Approved")
    REJECTED = "rejected", _("Rejected")


class ReasonRequestChoices(models.TextChoices):
    """Reasons choices for a request."""

    VACATION = "vacation", _("Planned vacation")
    SICK = "sick", _("Outpatient treatment")
    HOSPITAL = "hospital", _("Treatment with hospitalization")
