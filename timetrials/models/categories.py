from django.db import models
from django.utils.translation import gettext_lazy as _


# This isn't a model but I think it still belongs in the models module
class CategoryChoices(models.IntegerChoices):
    NON_SHORTCUT = 0, _("Non-Shortcut")
    """No ultra shortcuts nor community shortcuts may be used to be eligible"""

    SHORTCUT = 1, _("Shortcut")
    """No ultra shortcuts may be used to be eligible"""

    UNRESTRICTED = 2, _("Unrestricted")
    """No restrictions besides general rules"""
