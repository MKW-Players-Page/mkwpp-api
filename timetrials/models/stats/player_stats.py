from bisect import insort
from functools import reduce

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.regions import Region
from timetrials.models.standards import Standard
from timetrials.queries import query_ranked_scores, query_records


class PlayerStats(models.Model):
    """Precalculated fields for Player model"""

    player = models.ForeignKey(Player, related_name='stats', on_delete=models.CASCADE)

    # Category information

    region = models.ForeignKey(Region, related_name='playerstats', on_delete=models.CASCADE)

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

    total_record_ratio = models.FloatField(help_text=_("Sum of lowest score to record ratios"))

    total_records = models.IntegerField(help_test=_("Sum of track records"))

    leaderboard_points = models.IntegerField(help_text=_("Sum of leaderboard points"))

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

    mapped_standards = dict()

    for standard in Standard.objects.select_related('level').filter(level__is_legacy=True):
        for category in CategoryChoices.values:
            if standard.track_id not in mapped_standards:
                mapped_standards[standard.track_id] = dict()
            track_bucket = mapped_standards[standard.track_id]

            if category not in track_bucket:
                track_bucket[category] = dict()
            category_bucket = track_bucket[category]

            if standard.is_lap not in category_bucket:
                category_bucket[standard.is_lap] = list()
            lap_bucket = category_bucket[standard.is_lap]

            insort(lap_bucket, standard, key=lambda std: std.value or 60*60*1000)

    ranked_regions = dict(
        (region.id, region) for region in
        Region.objects.filter(is_ranked=True).order_by('pk')
    )

    mapped_records = dict()

    for region in ranked_regions.values():
        for category in CategoryChoices.values:
            records = query_records(category, region)
            for record in records:
                if record.track_id not in mapped_records:
                    mapped_records[record.track_id] = dict()
                track_bucket = mapped_records[record.track_id]

                if region.id not in track_bucket:
                    track_bucket[region.id] = dict()
                region_bucket = track_bucket[region.id]

                if category not in region_bucket:
                    region_bucket[category] = dict()
                category_bucket = region_bucket[category]

                category_bucket[record.is_lap] = record.value

    mapped_scores = dict()

    for region in ranked_regions.values():
        for category in CategoryChoices.values:
            scores = query_ranked_scores(category, region).order_by('player', 'is_lap')

            for score in scores:
                if score.player_id not in mapped_scores:
                    mapped_scores[score.player_id] = dict()
                player_bucket = mapped_scores[score.player_id]

                if region.id not in player_bucket:
                    player_bucket[region.id] = dict()
                region_bucket = player_bucket[region.id]

                if category not in region_bucket:
                    region_bucket[category] = dict()
                category_bucket = region_bucket[category]

                if score.is_lap not in category_bucket:
                    category_bucket[score.is_lap] = list()
                lap_bucket = category_bucket[score.is_lap]

                lap_bucket.append(score)

    PlayerStats.objects.all().delete()

    for player_id, player_bucket in mapped_scores.items():
        player = Player.objects.filter(id=player_id).first()

        with transaction.atomic():
            for region_id, region_bucket in player_bucket.items():
                region = ranked_regions[region_id]

                for category, category_bucket in region_bucket.items():
                    overall_stats = PlayerStats(
                        player=player,
                        region=region,
                        category=category,
                        is_lap=None
                    )
                    overall_stats.score_count = 0
                    overall_stats.total_score = 0
                    overall_stats.total_rank = 0
                    overall_stats.total_standard = 0
                    overall_stats.total_record_ratio = 0
                    overall_stats.total_records = 0
                    overall_stats.leaderboard_points = 0

                    for is_lap, scores in category_bucket.items():
                        stats = PlayerStats(
                            player=player,
                            region=region,
                            category=category,
                            is_lap=is_lap
                        )

                        stats.score_count = len(scores)
                        stats.total_score = reduce(
                            lambda total, score: total + score.value, scores, 0
                        )
                        stats.total_rank = reduce(
                            lambda total, score: total + score.rank, scores, 0
                        )
                        stats.total_standard = reduce(
                            lambda total, score: total + next(filter(
                                lambda std: std.value is None or std.value >= score.value,
                                mapped_standards[score.track_id][category][score.is_lap]
                            )).level.value,
                            scores,
                            0
                        )
                        stats.total_record_ratio = reduce(
                            lambda total, score:
                                total
                                + mapped_records[score.track_id][region.id][category][score.is_lap]
                                / score.value,
                            scores,
                            0
                        )
                        stats.total_records = reduce(

                        )
                        stats.leaderboard_points = reduce(
                            
                        )

                        overall_stats.score_count += stats.score_count
                        overall_stats.total_score += stats.total_score
                        overall_stats.total_rank += stats.total_rank
                        overall_stats.total_standard += stats.total_standard
                        overall_stats.total_record_ratio += stats.total_record_ratio
                        overall_stats.total_records += stats.total_records
                        overall_stats.leaderboard_points += stats.leaderboard_points

                        stats.save()

                    overall_stats.save()
