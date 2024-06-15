import logging

from celery import shared_task
from django.utils import timezone
from .models import Employee, DutyRoster


logger = logging.getLogger(__name__)


@shared_task
def update_duty_roster():
    """Task to update the duty roster."""

    today = timezone.now().date()
    next_saturday = today + timezone.timedelta(days=(5 - today.weekday()) % 7)
    next_sunday = next_saturday + timezone.timedelta(days=1)

    logger.info(
        f"Next Saturday: %s, Next Sunday: %s", next_saturday, next_sunday
    )

    # We receive all employees who can be on duty
    employees = Employee.objects.filter(can_duty=True).order_by("id")

    # We check whether there are employees on duty
    if not employees:
        logger.warning("No employees available for duty.")
        return

    # We get the last duty
    last_duty = DutyRoster.objects.order_by("id").last()

    if last_duty:
        # We find the index of the last employee
        last_employee_index = list(employees).index(last_duty.employee)
        next_employee = employees[(last_employee_index + 1) % len(employees)]

    else:
        # If this is the first duty
        next_employee = employees.first()

    logger.info(f"Next employee for duty: %s", next_employee)

    # We create a new record about duty
    new_duty = DutyRoster.objects.create(
        employee=next_employee, start_date=next_saturday, end_date=next_sunday
    )

    logger.info("New duty created: %s", new_duty)
