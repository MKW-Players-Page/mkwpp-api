from django import template

from timetrials.models import CategoryChoices
from timetrials.models.scores import value_to_string


register = template.Library()


@register.filter
def lap_mode(value):
    return "Lap" if value else "Course"


@register.filter
def category_name(value):
    return CategoryChoices(value).label


@register.filter
def format_score(value):
    return value_to_string(value)


@register.filter
def format_score_diff(value):
    return f"{'-' if value < 0 else '+'}{value_to_string(abs(value))}"
