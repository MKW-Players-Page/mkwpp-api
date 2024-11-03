from bisect import insort
from functools import reduce

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.regions import Region
from timetrials.models.scores import Score
from timetrials.models.standards import Standard
from timetrials.models.tracks import Track
from timetrials.queries import query_ranked_scores, query_records, query_region_players


class TopScoreCountChoices(models.IntegerChoices):
    ALL = 0, _("Every regional score")
    TOP_1 = 1, _("Regional record only")
    TOP_3 = 3, _("Top 3 regional scores")
    TOP_5 = 5, _("Top 5 regional scores")
    TOP_10 = 10, _("Top 10 regional scores")


class RegionStats(models.Model):
    region = models.ForeignKey(Region, related_name='stats', on_delete=models.CASCADE)

    # Category information

    top_score_count = models.IntegerField(
        choices=TopScoreCountChoices.choices,
        default=TopScoreCountChoices.TOP_1,
        help_text=_("Number of top region score per track"),
    )

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

    participation_count = models.IntegerField(
        help_text=_("Number of track-lap combination with enough scores to qualify")
    )

    score_count = models.IntegerField(help_text=_("Number of scores qualifying for the category"))

    total_score = models.BigIntegerField(help_text=_("Sum of all lowest scores"))

    total_rank = models.BigIntegerField(help_text=_("Sum of the rank of all lowest scores"))

    total_standard = models.BigIntegerField(help_text=_("Sum of the standard of all lowest scores"))

    total_record_ratio = models.FloatField(help_text=_("Sum of lowest score to record ratios"))

    total_records = models.IntegerField(help_text=_("Number of records"))

    def __str__(self):
        return "Region stats for %s - %s %s" % (
            self.region.name,
            CategoryChoices(self.category).label,
            "Overall" if self.is_lap is None else "Lap" if self.is_lap else "Course"
        )

    class Meta:
        verbose_name = _("region stats")
        verbose_name_plural = _("region stats")


def generate_all_region_stats():
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

    mapped_records = dict()

    for category in CategoryChoices.values:
        records = query_records(category)
        for record in records:
            if record.track_id not in mapped_records:
                mapped_records[record.track_id] = dict()
            track_bucket = mapped_records[record.track_id]

            if category not in track_bucket:
                track_bucket[category] = dict()
            category_bucket = track_bucket[category]

            category_bucket[record.is_lap] = record.value

    mapped_scores = dict()

    for category in CategoryChoices.values:
        scores = query_ranked_scores(category).order_by('track', 'is_lap', 'value')

        for region in Region.objects.all():
            region_players = query_region_players(region).values_list('pk', flat=True)

            for score in scores:
                if score.player_id not in region_players:
                    continue

                if region.id not in mapped_scores:
                    mapped_scores[region.id] = dict()
                region_bucket = mapped_scores[region.id]

                if category not in region_bucket:
                    region_bucket[category] = dict()
                category_bucket = region_bucket[category]

                if score.is_lap not in category_bucket:
                    category_bucket[score.is_lap] = dict()
                lap_bucket = category_bucket[score.is_lap]

                if score.track_id not in lap_bucket:
                    lap_bucket[score.track_id] = list()
                track_bucket = lap_bucket[score.track_id]

                track_bucket.append(score)

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

    for region_id, region_bucket in mapped_scores.items():
        for category in CategoryChoices.values:
            if category not in region_bucket:
                region_bucket[category] = dict()
            category_bucket = region_bucket[category]

            for is_lap in [False, True]:
                if is_lap not in category_bucket:
                    category_bucket[is_lap] = dict()
                lap_bucket = category_bucket[is_lap]

                for track_id in Track.objects.values_list('pk', flat=True):
                    pass

    RegionStats.objects.all().delete()

    for region_id, region_bucket in mapped_scores.items():
        with transaction.atomic():
            for category, category_bucket in region_bucket.items():
                for top_score_count in TopScoreCountChoices.values:
                    overall_stats = RegionStats(
                        region_id=region_id,
                        top_score_count=top_score_count,
                        category=category,
                        is_lap=None,
                    )
                    overall_stats.participation_count = 0
                    overall_stats.score_count = 0
                    overall_stats.total_score = 0
                    overall_stats.total_rank = 0
                    overall_stats.total_standard = 0
                    overall_stats.total_record_ratio = 0
                    overall_stats.total_records = 0

                    for is_lap in [False, True]:
                        stats = RegionStats(
                            region_id=region_id,
                            top_score_count=top_score_count,
                            category=category,
                            is_lap=is_lap,
                        )

                        lap_bucket = category_bucket.get(is_lap, dict())

                        stats.participation_count = len(list(filter(
                            lambda bucket: len(bucket) >= top_score_count, lap_bucket.values()
                        )))
                        stats.score_count = reduce(
                            lambda total, bucket: total + (
                                min(len(bucket), top_score_count) if top_score_count > 0
                                else len(bucket)
                            ),
                            lap_bucket.values(),
                            0
                        )

                        for track_id in Track.objects.values_list('pk', flat=True):
                            if track_id not in lap_bucket:
                                lap_bucket[track_id] = list()
                            bucket = lap_bucket[track_id]

                            missing = top_score_count - len(bucket)
                            if missing > 0:
                                bucket += [fallback_scores[category][is_lap][track_id]] * missing

                        stats.total_score = reduce(
                            lambda total, bucket: total + reduce(
                                lambda total, score: total + score.value,
                                bucket[:top_score_count] if top_score_count > 0 else bucket,
                                0
                            ),
                            lap_bucket.values(),
                            0
                        )
                        stats.total_rank = reduce(
                            lambda total, bucket: total + reduce(
                                lambda total, score: total + score.rank,
                                bucket[:top_score_count] if top_score_count > 0 else bucket,
                                0
                            ),
                            lap_bucket.values(),
                            0
                        )
                        stats.total_standard = reduce(
                            lambda total, bucket: total + reduce(
                                lambda total, score: total + next(filter(
                                    lambda std: std.value is None or std.value >= score.value,
                                    mapped_standards[score.track_id][category][score.is_lap]
                                )).level.value,
                                bucket[:top_score_count] if top_score_count > 0 else bucket,
                                0
                            ),
                            lap_bucket.values(),
                            0
                        )
                        stats.total_record_ratio = reduce(
                            lambda total, bucket: total + reduce(
                                lambda total, score:
                                    total
                                    + mapped_records[score.track_id][category][score.is_lap]
                                    / score.value,
                                bucket[:top_score_count] if top_score_count > 0 else bucket,
                                0
                            ),
                            lap_bucket.values(),
                            0
                        )
                        stats.total_records = reduce(
                            lambda total, bucket: total + (
                                1 if any(score.rank == 1 for score in (
                                    bucket[:top_score_count] if top_score_count > 0 else bucket
                                )) else 0
                            ),
                            lap_bucket.values(),
                            0
                        )

                        overall_stats.participation_count += stats.participation_count
                        overall_stats.score_count += stats.score_count
                        overall_stats.total_score += stats.total_score
                        overall_stats.total_rank += stats.total_rank
                        overall_stats.total_standard += stats.total_standard
                        overall_stats.total_record_ratio += stats.total_record_ratio
                        overall_stats.total_records += stats.total_records

                        stats.save()

                    overall_stats.save()
