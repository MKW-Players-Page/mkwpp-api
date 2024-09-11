from django.db.models import OuterRef, QuerySet, Subquery, Value, Window
from django.db.models.functions import NullIf, Rank

from rest_framework import generics

from timetrials import filters, models, serializers
from timetrials.models.categories import eligible_categories


class PlayerScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.filter(player=self.kwargs['pk'])

    def post_filter_queryset(self, queryset: QuerySet):
        categories = eligible_categories(
            self.request.query_params.get('category', models.CategoryChoices.NON_SHORTCUT)
        )

        # Get the player's lowest score on each track for both course and lap
        player_scores = queryset.order_by('track', 'is_lap', 'value').distinct('track', 'is_lap')

        # For each of the player's scores, query the lowest score from every player
        # on that same track and category
        track_scores = models.Score.objects.filter(
            track=OuterRef(OuterRef('track')),
            category__in=categories,
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
        return models.Score.objects.filter(
            pk__in=Subquery(player_scores.values('pk'))
        ).annotate(
            rank=Subquery(rank_subquery)
        ).order_by(
            'track', 'is_lap'
        )


class TrackScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.filter(track=self.kwargs['pk'])

    def post_filter_queryset(self, queryset: QuerySet):
        return models.Score.objects.filter(
            pk__in=Subquery(
                queryset.order_by('player', 'value').distinct('player').values('pk')
            )
        ).order_by(
            'value', 'date'
        ).annotate(rank=Window(Rank(), order_by='value'))


class RecordListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter

    def get_queryset(self):
        return models.Score.objects.order_by(
            'track', 'is_lap', 'value', 'date'
        ).distinct(
            'track', 'is_lap'
        ).annotate(rank=Value(1))
