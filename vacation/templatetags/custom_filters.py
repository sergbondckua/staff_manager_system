from datetime import datetime

from django import template

register = template.Library()


@register.filter
def calculate_percentage(value: int, max_value: int) -> int:
    """Calculate the percentage of value relative to max_value."""
    try:
        # Calculate percentage
        percentage = int((value / max_value) * 100)
    except (ValueError, ZeroDivisionError):
        # Handle division by zero or invalid value gracefully
        percentage = 0

    return percentage


@register.filter
def date_diff(start_date, end_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    delta = end_date - start_date
    return delta.days
