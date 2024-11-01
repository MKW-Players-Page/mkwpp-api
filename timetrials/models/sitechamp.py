from django.db import models
from django.utils import timezone

from timetrials.models import CategoryChoices, Player


class SiteChampion(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    date_instated = models.DateTimeField(default=timezone.now)

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT
    )

    def __str__(self):
        return f"{self.player} - {self.category}"
