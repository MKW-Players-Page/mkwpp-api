from functools import reduce

from django.db import models
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.regions import Region
from timetrials.models.scores import Score


class PlayerStats(models.Model):
    """Precalculated fields for Player model"""

    # Category information

    category = models.CharField(choices=CategoryChoices.choices)

    is_lap = models.BooleanField(
        null=True,
        blank=True,
        help_text=_("OFF for course, ON for lap, and null for both"),
    )

    # Stats

    score_count = models.IntegerField(help_text=_("Number of scores qualifying for the category"))

    total_score = models.IntegerField(help_text=_("Sum of all lowest scores"))

    total_rank = models.IntegerField(help_text=_("Sum of the rank of all lowest scores"))

    # Embedded player info

    player = models.ForeignKey(Player, related_name='stats', on_delete=models.CASCADE)

    player_name = models.CharField(max_length=64)

    player_region = models.ForeignKey(
        Region,
        related_name='playerstats',
        null=True,
        blank=False,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return "Stats for %s - %s %s" % (
            self.player_name,
            CategoryChoices(self.category).label,
            "Overall" if self.is_lap is None else "Lap" if self.is_lap else "Course"
        )

    class Meta:
        verbose_name = _("player stats")
        verbose_name_plural = _("player stats")


def generate_player_stats(player: Player):
    for category in CategoryChoices.values:
        for is_lap in [None, False, True]:
            stats = player.stats.filter(category=category, is_lap=is_lap).first()
            if not stats:
                stats = PlayerStats(
                    player=player,
                    player_name=player.name,
                    player_region=player.region,
                    category=category,
                    is_lap=is_lap,
                )

            scores = player.scores_for_category(category)
            if is_lap is not None:
                scores = scores.filter(is_lap=is_lap)

            stats.score_count = scores.count()
            if stats.score_count > 0:
                stats.total_score = (
                    Score.objects
                    .filter(pk__in=models.Subquery(scores.values('pk')))
                    .aggregate(models.Sum('value'))['value__sum']
                )
                stats.total_rank = reduce(
                    lambda total, score: total + score.rank_for_category(category), scores, 0
                )
            else:
                stats.total_score = 0
                stats.total_rank = 0

            stats.save()
