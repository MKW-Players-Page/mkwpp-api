from django.db import models
from django.utils.translation import gettext_lazy as _

from tree_queries.models import TreeNode


class RegionTypeChoices(models.TextChoices):
    WORLD = 'world', _("World")
    CONTINENT = 'continent', _("Continent")
    COUNTRY_GROUP = 'country_group', _("Country Group")
    COUNTRY = 'country', _("Country")
    SUBNATIONAL_GROUP = 'subnational_group', _("Subnational Group")
    SUBNATIONAL = 'subnational', _("Subnational")


class Region(TreeNode):
    type = models.CharField(max_length=32, choices=RegionTypeChoices.choices)

    name = models.CharField(max_length=64, unique=True)

    code = models.CharField(
        max_length=8,
        unique=True,
        help_text=_("ISO 2-letter code for countries, custom 3+ letters code otherwise.")
    )

    parent = models.ForeignKey(
        'self',
        related_name='children',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Parent region, or blank for top-most region (i.e. World).")
    )

    is_ranked = models.BooleanField(
        default=False,
        help_text=_("Whether this region has a dedicated tops chart and player rankings.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")
