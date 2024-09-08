from django.db import models
from django.utils.translation import gettext_lazy as _

from multiselectfield import MultiSelectField

from timetrials.models.categories import CategoryChoices


class TrackCup(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("cup")
        verbose_name_plural = _("cups")


class Track(models.Model):
    name = models.CharField(max_length=32)

    abbr = models.CharField(
        _("abbreviation"),
        max_length=8,
        help_text=_("E.g. LC for Luigi Circuit and rPB for GCN Peach Beach."),
    )

    cup = models.ForeignKey(
        TrackCup,
        related_name='tracks',
        on_delete=models.CASCADE,
    )

    categories = MultiSelectField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("track")
        verbose_name_plural = _("tracks")
