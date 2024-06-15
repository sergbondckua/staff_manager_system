from django.db import models
from django.db.models.signals import post_save, post_migrate, post_delete
from django.dispatch import receiver

from common.enums import StatusRequestChoices
from vacation.models import LeaveRequest, LeaveType, VacationUsed


def update_vacation_used(instance=None):
    if instance.status == StatusRequestChoices.APPROVED:
        total_days = (
            LeaveRequest.objects.filter(
                employee=instance.employee,
                status=StatusRequestChoices.APPROVED,
                expired=False,
            ).aggregate(total=models.Sum("number_of_days"))["total"]
            or 0
        )

        vacation_used, created = VacationUsed.objects.get_or_create(
            employee=instance.employee
        )
        vacation_used.days = total_days
        vacation_used.save()


@receiver(post_migrate)
def create_default_leave_type(sender, **kwargs):
    """Signal handler that creates default leave types after migrations are applied."""
    if sender.name == "vacation":  # Creating leave type for 'vacation'
        annual, _ = LeaveType.objects.get_or_create(
            title="Annual", parent=None
        )
        sick, _ = LeaveType.objects.get_or_create(title="Sick", parent=None)
        LeaveType.objects.get_or_create(title="Home", parent=sick)
        LeaveType.objects.get_or_create(title="Hospital", parent=sick)


@receiver(post_delete, sender=LeaveRequest)
def post_delete_leave_request(sender, instance, **kwargs):
    """Counts the number of used vacation days after deleting the record."""
    update_vacation_used(instance)


@receiver(post_save, sender=LeaveRequest)
def post_save_leave_request(sender, instance, **kwargs):
    """Update the number of used vacation days after saving the record."""
    update_vacation_used(instance)
