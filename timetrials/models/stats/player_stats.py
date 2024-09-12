from functools import reduce

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from timetrials.queries import annotate_scores_standard, query_ranked_scores
from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.regions import Region
from timetrials.models.standards import Standard


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

    total_standard = models.IntegerField(help_text=_("Sum of the standard of all lowest scores"))

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

    @classmethod
    def get_or_new(cls, player: Player, category: CategoryChoices, is_lap: bool):
        """Get or create a PlayerStats instance *without saving to the DB*."""
        return (
            player.stats.filter(category=category, is_lap=is_lap).first()
            or
            PlayerStats(
                player=player,
                player_name=player.name,
                player_region=player.region,
                category=category,
                is_lap=is_lap,
            )
        )

    class Meta:
        verbose_name = _("player stats")
        verbose_name_plural = _("player stats")


def generate_all_player_stats():
    """Recalculate player stats for all players"""

    # Map each standard's id to the value of its related level
    standard_values = dict((id, value) for [id, value] in Standard.objects.filter(
        level__is_legacy=True
    ).select_related('level').annotate(
        level_value=models.F('level__value')
    ).values_list('id', 'level_value'))

    mapped_scores = dict()

    for category in CategoryChoices.values:
        scores = query_ranked_scores(category).order_by('player', 'is_lap')
        scores = annotate_scores_standard(scores, category, legacy=True)

        for score in scores:
            if score.player_id not in mapped_scores:
                mapped_scores[score.player_id] = dict()
            player_bucket = mapped_scores[score.player_id]

            if category not in player_bucket:
                player_bucket[category] = dict()
            category_bucket = player_bucket[category]

            if score.is_lap not in category_bucket:
                category_bucket[score.is_lap] = list()
            lap_bucket = category_bucket[score.is_lap]

            lap_bucket.append(score)

    for player_id, player_buckets in mapped_scores.items():
        player = Player.objects.filter(id=player_id).first()

        with transaction.atomic():
            for category, category_buckets in player_buckets.items():
                overall_stats = PlayerStats.get_or_new(player, category, None)
                overall_stats.score_count = 0
                overall_stats.total_score = 0
                overall_stats.total_rank = 0
                overall_stats.total_standard = 0

                for is_lap, scores in category_buckets.items():
                    stats = PlayerStats.get_or_new(player, category, is_lap)

                    stats.score_count = len(scores)
                    stats.total_score = reduce(lambda total, score: total + score.value, scores, 0)
                    stats.total_rank = reduce(lambda total, score: total + score.rank, scores, 0)
                    stats.total_standard = reduce(
                        lambda total, score: total + standard_values[score.standard],
                        scores,
                        0
                    )

                    overall_stats.score_count += stats.score_count
                    overall_stats.total_score += stats.total_score
                    overall_stats.total_rank += stats.total_rank
                    overall_stats.total_standard += stats.total_standard

                    stats.save()

                overall_stats.save()
