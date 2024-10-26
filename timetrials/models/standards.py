from django.db import models
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.tracks import Track


class StandardLevel(models.Model):
    name = models.CharField(max_length=64)

    value = models.IntegerField(
        help_text=_("Points awarded for achieving this standard level. The lower the better."),
    )

    is_legacy = models.BooleanField(
        help_text=_("Whether this was part of the original 2010s standard set.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("standard level")
        verbose_name_plural = _("standard levels")


class Standard(models.Model):
    level = models.ForeignKey(
        StandardLevel,
        related_name='standards',
        on_delete=models.CASCADE,
    )

    track = models.ForeignKey(
        Track,
        related_name='standards',
        on_delete=models.CASCADE,
    )

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT,
    )

    is_lap = models.BooleanField(default=False, help_text=_("Off for 3lap, on for flap."))

    value = models.IntegerField(
        _("threshold"),
        null=True,
        blank=True,
        help_text=_("The highest score which qualifies for this standard. "
                    "Leave blank for a catch-all standard."),
    )

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = _("standard")
        verbose_name_plural = _("standards")

        constraints = [
            models.UniqueConstraint('level', 'track', 'category', 'is_lap',
                                    name='unique_by_level_track_category_lap'),
        ]
