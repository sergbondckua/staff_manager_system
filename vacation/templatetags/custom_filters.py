from datetime import datetime, date

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
def date_diff(start_date: [str, date], end_date: [str, date]) -> int:
    """
    Calculate the difference in days between two dates.

    Args:
        start_date (str or date): The start date. If None, defaults to January 1st of the current year.
        end_date (str or date): The end date.

    Returns:
        int: The number of days between start_date and end_date.
    """
    try:
        # If start_date is not provided, set it to January 1st of the current year
        if not start_date:
            start_date = date(datetime.now().year, 1, 1)

        # Convert string dates to date objects
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Calculate the difference in days
        delta = end_date - start_date
        return delta.days
    except Exception as e:
        return 0
