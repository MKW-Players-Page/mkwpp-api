from django.db.models import Subquery, Window
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
        'track', 'is_lap', 'player'
    ).order_by(
        'track', 'is_lap', 'player', 'value'
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
