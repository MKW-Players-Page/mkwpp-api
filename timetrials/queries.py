from django.db.models import F, FloatField, OuterRef, Q, QuerySet, Subquery, Value, Window
from django.db.models.functions import Cast, Rank

from django_cte import With

from timetrials import models


def query_region_players(region: models.Region):
    """Query players from a given region, including all sub-regions."""

    return models.Player.objects.filter(
        region__in=region.descendants(include_self=True).values_list('pk', flat=True)
    )


def query_records(category: models.CategoryChoices, region: models.Region = None):
    """
    Query records across all tracks for a given category and region.
    If no category is specified, the overall records will be queried.
    """

    records = models.Score.objects.distinct(
        'track', 'is_lap'
    ).order_by(
        'track', 'is_lap', 'value'
    ).filter(
        category__lte=category,
    ).annotate(
        rank=Value(1)
    )

    if region and region.type != models.RegionTypeChoices.WORLD:
        records = records.filter(
            player__in=Subquery(query_region_players(region).values('pk'))
        )

    return records


def query_ranked_scores(category: models.CategoryChoices, region: models.Region = None):
    """
    Query all players' records across all tracks for a given category and
    annotate each score's rank.
    """

    player_records = models.Score.objects.distinct(
        'player', 'track', 'is_lap'
    ).order_by(
        'player', 'track', 'is_lap', 'value'
    ).filter(
        category__lte=category,
    ).values('pk')

    ranked_scores_query = models.Score.objects.order_by(
        'track', 'is_lap'
    ).filter(
        pk__in=Subquery(player_records)
    )

    if region and region.type != models.RegionTypeChoices.WORLD:
        ranked_scores_query = ranked_scores_query.filter(
            player__in=Subquery(query_region_players(region).values('pk'))
        )

    ranked_scores = With(
        ranked_scores_query.annotate(
            rank=Window(Rank(), partition_by=['track', 'is_lap'], order_by=['value'])
        ),
        name='ranked_scores'
    )

    return ranked_scores.queryset().with_cte(ranked_scores)


def annotate_scores_standard(scores: QuerySet, category: models.CategoryChoices, legacy=False):
    """
    Annotates each score within the queryset with the id of the highest standard level it qualifies
    for given a category. Legacy standards may be used optionally.
    """

    return scores.annotate(
        standard=Subquery(
            models.Standard.objects.filter(
                Q(value__gte=OuterRef('value')) | Q(value=None),
                track=OuterRef('track'),
                category__lte=category,
                is_lap=OuterRef('is_lap'),
                level__is_legacy=legacy,
            ).order_by(
                '-category',
                'value'
            ).values('level')[:1]
        )
    )


def annotate_scores_record_ratio(scores: QuerySet,
                                 category: models.CategoryChoices,
                                 region: models.Region | None = None):
    """Annotate each score within the queryset with its record ratio."""

    records = models.Score.objects.distinct(
        'track', 'is_lap'
    ).order_by(
        'track', 'is_lap', 'value'
    ).filter(
        category__lte=category
    )

    if region is not None:
        if region.type != models.RegionTypeChoices.WORLD:
            records = records.filter(
                player__in=Subquery(query_region_players(region).values('pk'))
            )

    return scores.annotate(
        record_ratio=Subquery(
            models.Score.objects.filter(
                pk__in=records.values('pk')
            ).filter(
                track=OuterRef('track'),
                is_lap=OuterRef('is_lap')
            ).values('value')
        ) / Cast(F('value'), FloatField())
    )
