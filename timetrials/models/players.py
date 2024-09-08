from django.db import models
from django.utils.timezone import datetime
from django.utils.translation import gettext_lazy as _

from core.models import User
from timetrials.models.regions import Region, RegionTypeChoices


class Player(models.Model):
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("User account associated with this player profile.")
    )

    name = models.CharField(max_length=64, unique=True)

    region = models.ForeignKey(
        Region,
        related_name='players',
        limit_choices_to={'type__in': (RegionTypeChoices.COUNTRY, RegionTypeChoices.SUBNATIONAL)},
        null=True,
        blank=False,
        on_delete=models.SET_NULL
    )

    alias = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text=_("Can be anything, but is meant to be the player's online pseudonym.")
    )

    joined_date = models.DateField(null=True, blank=True, default=datetime.today)
    last_activity = models.DateField(null=True, blank=True)

    bio = models.TextField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("player")
        verbose_name_plural = _("players")
