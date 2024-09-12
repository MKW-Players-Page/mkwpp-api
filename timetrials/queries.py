from django.db.models import Case, OuterRef, Q, QuerySet, Subquery, Value, When, Window
from django.db.models.functions import Rank

from django_cte import With

from timetrials import models
from timetrials.models.categories import eligible_categories


def query_ranked_scores(category: models.CategoryChoices):
    """
    Query all players' records across all tracks for a given category and
    annotate each score's rank.
    """

    player_records = models.Score.objects.distinct(
        'player', 'track', 'is_lap'
    ).order_by(
        'player', 'track', 'is_lap', 'value'
    ).filter(
        category__in=eligible_categories(category)
    ).values('pk')

    ranked_scores = With(
        models.Score.objects.order_by(
            'track', 'is_lap'
        ).filter(
            pk__in=Subquery(player_records)
        ).annotate(
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
                category__in=eligible_categories(category),
                is_lap=OuterRef('is_lap'),
                level__is_legacy=legacy,
            ).order_by(
                Case(
                    When(category='unres', then=Value(1)),
                    When(category='sc', then=Value(2)),
                    When(category='nonsc', then=Value(3)),
                ),
                'value'
            ).values('pk')[:1]
        )
    )
