from django.db import models
from django.utils.translation import gettext_lazy as _


# This isn't a model but I think it still belongs in the models module
class CategoryChoices(models.TextChoices):
    NON_SHORTCUT = 'nonsc', _("Non-Shortcut")
    """No ultra shortcuts nor community shortcuts may be used to be eligible"""

    SHORTCUT = 'sc', _("Shortcut")
    """No ultra shortcuts may be used to be eligible"""

    UNRESTRICTED = 'unres', _("Unrestricted")
    """No restrictions besides general rules"""


def eligible_categories(category: CategoryChoices):
    """
    Return all categories eligible for a given category. For example, eligible categories for
    SHORTCUT are SHORTCUT, since it is the category itself, as well as NON_SHORTCUT, since the
    rules of SHORTCUT all apply to NON_SHORTCUT. NON_SHORTCUT returns only itself since it is has
    the most restrictive ruleset, and UNRESTRICTED returns all categories, since it has no rules.
    """
    return CategoryChoices.values[:CategoryChoices.values.index(category) + 1]
