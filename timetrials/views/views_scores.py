from django.db.models import OuterRef, QuerySet, Subquery, Value, Window
from django.db.models.functions import NullIf, Rank
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics

from timetrials import filters, models, serializers
from timetrials.models.categories import eligible_categories
from timetrials.queries import annotate_scores_standard


@method_decorator(cache_page(60), name='list')
class PlayerScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.filter(player=self.kwargs['pk'])

    def post_filter_queryset(self, queryset: QuerySet):
        category = self.request.query_params.get('category', models.CategoryChoices.NON_SHORTCUT)

        # Get the player's lowest score on each track for both course and lap
        player_scores = queryset.order_by('track', 'is_lap', 'value').distinct('track', 'is_lap')

        # For each of the player's scores, query the lowest score from every player
        # on that same track and category
        track_scores = models.Score.objects.filter(
            track=OuterRef(OuterRef('track')),
            category__in=eligible_categories(category),
            is_lap=OuterRef(OuterRef('is_lap'))
        ).order_by('player', 'value').distinct('player')

        # Calculate the rank of each score from the previous query and extract only
        # the rank of the player's score
        rank_subquery = models.Score.objects.filter(
            pk__in=Subquery(track_scores.values('pk'))
        ).annotate(
            rank=Window(Rank(), order_by='value')
        ).order_by(
            NullIf('player', self.kwargs['pk']).desc()
        ).values('rank')[:1]

        # Annotate the player's lowest scores with their rank and order by track and lap count
        scores = models.Score.objects.filter(
            pk__in=Subquery(player_scores.values('pk'))
        ).annotate(
            rank=Subquery(rank_subquery)
        ).order_by(
            'track', 'is_lap'
        )

        return annotate_scores_standard(scores, category, legacy=True)


@method_decorator(cache_page(60), name='list')
class TrackScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.filter(track=self.kwargs['pk'])

    def post_filter_queryset(self, queryset: QuerySet):
        scores = models.Score.objects.filter(
            pk__in=Subquery(
                queryset.order_by('player', 'value').distinct('player').values('pk')
            )
        ).order_by(
            'value', 'date'
        ).annotate(rank=Window(Rank(), order_by='value'))

        return annotate_scores_standard(
            scores,
            self.request.query_params.get('category', models.CategoryChoices.NON_SHORTCUT),
            legacy=True
        )


@method_decorator(cache_page(60), name='list')
class RecordListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.all()

    def post_filter_queryset(self, queryset: QuerySet):
        records = queryset.order_by(
            'track', 'is_lap', 'value', 'date'
        ).distinct(
            'track', 'is_lap'
        )

        scores = models.Score.objects.filter(
            pk__in=Subquery(records.values('pk'))
        ).annotate(
            rank=Value(1)
        )

        return annotate_scores_standard(
            scores,
            self.request.query_params.get('category', models.CategoryChoices.NON_SHORTCUT),
            legacy=True
        )
