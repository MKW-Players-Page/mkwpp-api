from bisect import insort
from collections import defaultdict
from functools import reduce

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.regions import Region
from timetrials.models.standards import Standard
from timetrials.models.tracks import Track
from timetrials.queries import query_ranked_scores


class PlayerStatsGroup(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return str(timezone.datetime.strftime(self.created_at, "%Y-%m-%d %H:%M:%S"))


class PlayerStats(models.Model):
    """Precalculated fields for Player model"""

    group = models.ForeignKey(PlayerStatsGroup, related_name='stats', on_delete=models.CASCADE)

    player = models.ForeignKey(Player, related_name='stats', on_delete=models.CASCADE)

    # Category information

    region = models.ForeignKey(Region, related_name='playerstats', on_delete=models.CASCADE)

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT,
    )

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

    total_record_ratio = models.FloatField(help_text=_("Sum of lowest score to record ratios"))

    total_records = models.IntegerField(help_text=_("Number of records"))

    leaderboard_points = models.IntegerField(help_text=_("Sum of leaderboard points"))

    @property
    def effective_score_count(self):
        """
        The actual number of scores counted in the tallies, including fallback scores when necessary
        """
        return Track.objects.count() * (2 if self.is_lap is None else 1)

    def __str__(self):
        return "Stats for %s - %s %s" % (
            self.player.name,
            CategoryChoices(self.category).label,
            "Overall" if self.is_lap is None else "Lap" if self.is_lap else "Course"
        )

    class Meta:
        verbose_name = _("player stats")
        verbose_name_plural = _("player stats")


def generate_all_player_stats():
    """Recalculate player stats for all players"""

    track_ids = tuple(Track.objects.values_list('pk', flat=True))
    lap_modes = (False, True)

    mapped_standards = {
        track_id: {
            is_lap: {
                category: list()
                for category in CategoryChoices.values
            }
            for is_lap in lap_modes
        }
        for track_id in track_ids
    }

    for category in CategoryChoices.values:
        standards = Standard.objects.filter(
            category__lte=category,
            level__is_legacy=True,
        ).distinct(
            'track', 'is_lap', 'level'
        ).order_by(
            'track', 'is_lap', 'level', '-category'
        ).values('track', 'is_lap', 'level__value', 'value')
        for standard in standards:
            bucket = mapped_standards[standard['track']][standard['is_lap']][category]
            insort(bucket, standard, key=lambda standard: standard['level__value'])

    ranked_regions = tuple(Region.objects.filter(is_ranked=True).order_by('pk'))

    fallback_scores = {
        track_id: {
            is_lap: dict()
            for is_lap in lap_modes
        }
        for track_id in track_ids
    }

    for category in CategoryChoices.values:
        bottom_scores = query_ranked_scores(category).distinct(
            'track', 'is_lap'
        ).order_by(
            'track', 'is_lap', '-value'
        ).values(
            'track', 'is_lap', 'value', 'rank'
        )
        for score in bottom_scores:
            fallback_scores[score['track']][score['is_lap']][category] = {
                'track': score['track'],
                'is_lap': score['is_lap'],
                'value': score['value'] + 1,
                'rank': score['rank'] + 1,
                'is_fallback': True,
            }

    mapped_records = {
        track_id: {
            is_lap: {
                category: dict()
                for category in CategoryChoices.values
            }
            for is_lap in lap_modes
        }
        for track_id in track_ids
    }

    mapped_scores = {
        player_id: defaultdict(lambda: {
            category: {
                is_lap: {
                    track_id: fallback_scores[track_id][is_lap][category]
                    for track_id in track_ids
                }
                for is_lap in lap_modes
            }
            for category in CategoryChoices
        })
        for player_id in Player.objects.values_list('pk', flat=True)
    }

    for region in ranked_regions:
        for category in CategoryChoices.values:
            scores = query_ranked_scores(category, region).order_by(
                'player', 'is_lap'
            ).values(
                'player', 'track', 'is_lap', 'value', 'rank'
            )
            for score in scores:
                bucket = mapped_scores[score['player']][region.id]
                bucket[category][score['is_lap']][score['track']] = score
                if score['rank'] == 1:
                    record_bucket = mapped_records[score['track']][score['is_lap']][category]
                    record_bucket[region.id] = score['value']

    group = PlayerStatsGroup.objects.create()

    stats_objects = list()

    for player_id, player_bucket in mapped_scores.items():
        for region_id, region_bucket in player_bucket.items():
            for category, category_bucket in region_bucket.items():
                overall_stats = PlayerStats(
                    group=group,
                    player_id=player_id,
                    region_id=region_id,
                    category=category,
                    is_lap=None,
                    score_count=0,
                    total_score=0,
                    total_rank=0,
                    total_standard=0,
                    total_record_ratio=0,
                    total_records=0,
                    leaderboard_points=0,
                )

                for is_lap, scores in category_bucket.items():
                    stats = PlayerStats(
                        group=group,
                        player_id=player_id,
                        region_id=region_id,
                        category=category,
                        is_lap=is_lap,
                        score_count=0,
                        total_score=0,
                        total_rank=0,
                        total_standard=0,
                        total_record_ratio=0,
                        total_records=0,
                        leaderboard_points=0,
                    )

                    stats.score_count = reduce(
                        lambda total, score: total + (0 if score.get('is_fallback', False) else 1),
                        scores.values(),
                        0
                    )
                    stats.total_score = reduce(
                        lambda total, score: total + score['value'], scores.values(), 0
                    )
                    stats.total_rank = reduce(
                        lambda total, score: total + score['rank'], scores.values(), 0
                    )
                    stats.total_standard = reduce(
                        lambda total, score: total + next(filter(
                            lambda std: std['value'] is None or std['value'] >= score['value'],
                            mapped_standards[score['track']][score['is_lap']][category]
                        ))['level__value'],
                        scores.values(),
                        0
                    )
                    stats.total_record_ratio = reduce(
                        lambda total, score:
                            total
                            + mapped_records[score['track']][score['is_lap']][category][region_id]
                            / score['value'],
                        scores.values(),
                        0
                    )
                    stats.total_records = sum(map(
                        lambda score: 1 if score['rank'] == 1 else 0, scores.values()
                    ))
                    stats.leaderboard_points = sum(map(
                        lambda score: max(11 - score['rank'], 0), scores.values()
                    ))

                    overall_stats.score_count += stats.score_count
                    overall_stats.total_score += stats.total_score
                    overall_stats.total_rank += stats.total_rank
                    overall_stats.total_standard += stats.total_standard
                    overall_stats.total_record_ratio += stats.total_record_ratio
                    overall_stats.total_records += stats.total_records
                    overall_stats.leaderboard_points += stats.leaderboard_points

                    stats_objects.append(stats)

                stats_objects.append(overall_stats)

    PlayerStats.objects.bulk_create(stats_objects)

    group.completed = True
    group.save()
