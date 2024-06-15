import logging

from celery import shared_task
from django.db import transaction

from common.enums import StatusRequestChoices
from vacation.models import VacationUsed, LeaveRequest

logger = logging.getLogger(__name__)


@shared_task
def reset_vacations_used_days():
    """Reset the number of days."""

    # Use a transaction to ensure atomicity and integrity
    with transaction.atomic():
        # Bulk update to reset all days to 0
        VacationUsed.objects.all().update(days=0)
        LeaveRequest.objects.filter(
            status=StatusRequestChoices.APPROVED
        ).update(expired=True)

    logger.info("Successfully reset all vacation used days to 0.")
