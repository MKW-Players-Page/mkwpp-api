from bisect import insort
from functools import reduce

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.regions import Region
from timetrials.models.scores import Score
from timetrials.models.standards import Standard
from timetrials.models.tracks import Track
from timetrials.queries import query_ranked_scores, query_records


class PlayerStats(models.Model):
    """Precalculated fields for Player model"""

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

    mapped_standards = dict()

    for category in CategoryChoices.values:
        standards = Standard.objects.select_related('level').filter(
            category__lte=category,
            level__is_legacy=True,
        ).distinct(
            'track', 'is_lap', 'level'
        ).order_by(
            'track', 'is_lap', 'level', '-category'
        )
        for standard in standards:
            if standard.track_id not in mapped_standards:
                mapped_standards[standard.track_id] = dict()
            track_bucket = mapped_standards[standard.track_id]

            if category not in track_bucket:
                track_bucket[category] = dict()
            category_bucket = track_bucket[category]

            if standard.is_lap not in category_bucket:
                category_bucket[standard.is_lap] = list()
            lap_bucket = category_bucket[standard.is_lap]

            insort(lap_bucket, standard, key=lambda std: std.level.value)

    ranked_regions = dict(
        (region.id, region) for region in
        Region.objects.filter(is_ranked=True).order_by('pk')
    )

    fallback_scores = dict()

    for category in CategoryChoices.values:
        bottom_scores = query_ranked_scores(category).distinct(
            'track', 'is_lap'
        ).order_by(
            'track', 'is_lap', '-value'
        )
        for score in bottom_scores:
            if category not in fallback_scores:
                fallback_scores[category] = dict()
            category_bucket = fallback_scores[category]

            if score.is_lap not in category_bucket:
                category_bucket[score.is_lap] = dict()
            lap_bucket = category_bucket[score.is_lap]

            fallback_score = Score(
                value=score.value + 1,
                track=score.track,
                is_lap=score.is_lap,
            )
            fallback_score.rank = score.rank + 1
            fallback_score.is_fallback = True
            lap_bucket[score.track_id] = fallback_score

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

    def make_score_bucket():
        new_score_bucket = dict()
        for category, category_bucket in fallback_scores.items():
            new_category_bucket = new_score_bucket[category] = dict()
            for is_lap, lap_bucket in category_bucket.items():
                new_lap_bucket = new_category_bucket[is_lap] = dict()
                for track_id, score in lap_bucket.items():
                    new_lap_bucket[track_id] = score

        return new_score_bucket

    for region in ranked_regions.values():
        for category in CategoryChoices.values:
            scores = query_ranked_scores(category, region).order_by('player', 'is_lap')

            for score in scores:
                if score.player_id not in mapped_scores:
                    mapped_scores[score.player_id] = dict()
                player_bucket = mapped_scores[score.player_id]

                if region.id not in player_bucket:
                    player_bucket[region.id] = make_score_bucket()
                region_bucket = player_bucket[region.id]

                region_bucket[category][score.is_lap][score.track_id] = score

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

                        stats.score_count = len(list(filter(
                            lambda score: not getattr(score, 'is_fallback', False), scores.values()
                        )))
                        stats.total_score = reduce(
                            lambda total, score: total + score.value, scores.values(), 0
                        )
                        stats.total_rank = reduce(
                            lambda total, score: total + score.rank, scores.values(), 0
                        )
                        stats.total_standard = reduce(
                            lambda total, score: total + next(filter(
                                lambda std: std.value is None or std.value >= score.value,
                                mapped_standards[score.track_id][category][score.is_lap]
                            )).level.value,
                            scores.values(),
                            0
                        )
                        stats.total_record_ratio = reduce(
                            lambda total, score:
                                total
                                + mapped_records[score.track_id][region.id][category][score.is_lap]
                                / score.value,
                            scores.values(),
                            0
                        )

                        stats.total_records = len(list(filter(
                            lambda score: score.rank == 1, scores.values()
                        )))

                        stats.leaderboard_points = sum(map(
                            lambda score: max(11 - score.rank, 0), scores.values()
                        ))

                        overall_stats.score_count += stats.score_count
                        overall_stats.total_score += stats.total_score
                        overall_stats.total_rank += stats.total_rank
                        overall_stats.total_standard += stats.total_standard
                        overall_stats.total_record_ratio += stats.total_record_ratio
                        overall_stats.total_records += stats.total_records
                        overall_stats.leaderboard_points += stats.leaderboard_points

                        stats.save()

                    overall_stats.save()
