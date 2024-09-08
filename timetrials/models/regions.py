from django.db import models
from django.utils.translation import gettext_lazy as _


class RegionTypeChoices(models.TextChoices):
    WORLD = 'world', _("World")
    CONTINENT = 'continent', _("Continent")
    COUNTRY = 'country', _("Country")
    SUBNATIONAL = 'subnational', _("Subnational")


class Region(models.Model):
    type = models.CharField(max_length=16, choices=RegionTypeChoices.choices)

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")
