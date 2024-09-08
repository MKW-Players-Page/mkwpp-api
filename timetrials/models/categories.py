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
