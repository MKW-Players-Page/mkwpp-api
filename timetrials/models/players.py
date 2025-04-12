from django.conf import settings
from django.db import models
from django.utils.timezone import datetime
from django.utils.translation import gettext_lazy as _

from timetrials.models.regions import Region


class Player(models.Model):
    name = models.CharField(max_length=64, unique=True)

    region = models.ForeignKey(
        Region,
        related_name='players',
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


class PlayerAwardTypeChoices(models.TextChoices):
    WEEKLY = 'weekly', _("Weekly")
    QUARTERLY = 'quarterly', _("Quarterly")
    MONTHLY = 'monthly', _("Monthly")
    YEARLY = 'yearly', _("Yearly")


class PlayerAward(models.Model):
    player = models.ForeignKey(Player, related_name='awards', on_delete=models.CASCADE)

    type = models.CharField(
        choices=PlayerAwardTypeChoices.choices,
        default=PlayerAwardTypeChoices.WEEKLY
    )

    date = models.DateField(default=datetime.today)

    description = models.CharField(max_length=1024)


class PlayerSubmitter(models.Model):
    player = models.ForeignKey(
        Player,
        related_name='submitters',
        on_delete=models.CASCADE,
        help_text=_("The player the submitter is granted permission to create submissions for."),
    )

    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='submittees',
        on_delete=models.CASCADE,
        help_text=_("The user being granted permission to create submissions for the player."),
    )

    class Meta:
        verbose_name = _("player submitter")
        verbose_name_plural = _("player submitters")

        constraints = [
            models.UniqueConstraint(fields=['player', 'submitter'], name='unique_player_submitter'),
        ]
