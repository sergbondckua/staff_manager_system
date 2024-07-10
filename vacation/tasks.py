import asyncio
import logging

from celery import shared_task
from django.db import transaction

from common.enums import StatusRequestChoices
from telegrambot.bot import bot

logger = logging.getLogger(__name__)


@shared_task
def reset_vacations_used_days():
    """Reset the number of days."""

    from vacation.models import VacationUsed, LeaveRequest

    # Use a transaction to ensure atomicity and integrity
    with transaction.atomic():
        # Bulk update to reset all days to 0
        VacationUsed.objects.all().update(days=0)
        LeaveRequest.objects.filter(
            status=StatusRequestChoices.APPROVED
        ).update(expired=True)

    logger.info("Successfully reset all vacation used days to 0.")


@shared_task
def send_vacation_request_for_approval(text: str):
    """Send a vacation request to management for approval"""

    from staff.models import Employee

    managements = Employee.objects.filter(
        telegram_id__isnull=False,
        is_staff=True,
        is_active=True,
        groups__isnull=False,
    )
    if not managements.exists():
        logger.warning("No active management users found to send message.")
        return

    try:
        loop = asyncio.get_event_loop()
        tasks = [
            bot.send_message(chat_id.telegram_id, text)
            for chat_id in managements
        ]
        loop.run_until_complete(asyncio.gather(*tasks))
    except Exception as e:
        logger.error("Failed to send message: %s", e)
