from django import template

register = template.Library()


@register.filter
def calculate_percentage(value: float, max_value: float) -> int:
    """Calculate the percentage of value relative to max_value."""
    try:
        # Calculate percentage
        percentage = int((value / max_value) * 100)
    except (ValueError, ZeroDivisionError):
        # Handle division by zero or invalid value gracefully
        percentage = 0

    return percentage
