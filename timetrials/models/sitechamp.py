from django.db import models
from django.utils import timezone
from .players import Player

from timetrials.models.categories import CategoryChoices

class SiteChampion(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    date_became_champion = models.DateTimeField(default=timezone.now)

    category = models.CharField(max_length=10, choices=CategoryChoices.choices)

    def __str__(self):
        return f"{self.player} - {self.category}"