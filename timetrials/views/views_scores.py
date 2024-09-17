from django.db.models import OuterRef, Subquery, Value, Window
from django.db.models.functions import NullIf, Rank
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics

from timetrials import filters, models, serializers
from timetrials.models.categories import eligible_categories
from timetrials.queries import (
    annotate_scores_record_ratio, annotate_scores_standard, query_region_players
)


@method_decorator(cache_page(60), name='list')
@filters.extend_schema_with_filters
class PlayerScoreListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.ScoreSerializer
    filter_fields = (
        filters.CategoryFilter(),
        filters.LapModeFilter(required=False),
    )

    def get_queryset(self):
        # Get the player's lowest score on each track for both course and lap
        player_scores = self.filter(models.Score.objects).filter(
            player=self.kwargs['pk']
        ).order_by(
            'track', 'is_lap', 'value'
        ).distinct(
            'track', 'is_lap'
        )

        category = self.get_filter_value(filters.CategoryFilter)

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

        return annotate_scores_record_ratio(
            annotate_scores_standard(scores, category, legacy=True),
            category
        )


@method_decorator(cache_page(60), name='list')
@filters.extend_schema_with_filters
class TrackScoreListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_fields = (
        filters.CategoryFilter(),
        filters.LapModeFilter(),
    )

    def get_queryset(self):
        scores = models.Score.objects.filter(
            pk__in=Subquery(
                self.filter(models.Score.objects).filter(
                    track=self.kwargs['pk']
                ).order_by(
                    'player', 'value'
                ).distinct(
                    'player'
                ).values('pk')
            )
        ).order_by(
            'value', 'date'
        ).annotate(rank=Window(Rank(), order_by='value'))

        category = self.get_filter_value(filters.CategoryFilter)

        return annotate_scores_record_ratio(
            annotate_scores_standard(scores, category, legacy=True),
            category
        )


@method_decorator(cache_page(60), name='list')
@filters.extend_schema_with_filters
class TrackTopsListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_fields = (
        filters.CategoryFilter(),
        filters.LapModeFilter(),
        filters.RegionFilter(ranked_only=True, auto=False, required=False),
    )

    def get_queryset(self):
        scores = self.filter(models.Score.objects).filter(
            track=self.kwargs['pk']
        ).order_by(
            'value', 'date'
        ).annotate(
            rank=Window(Rank(), order_by='value'),
            record_ratio=Value(1),
            standard=Value(1),
        ).filter(
            rank__lte=10
        )

        region = self.get_filter_value(filters.RegionFilter)

        if region and region.type != models.RegionTypeChoices.WORLD:
            scores = scores.filter(
                player__in=Subquery(query_region_players(region).values('pk'))
            )

        category = self.get_filter_value(filters.CategoryFilter)

        return annotate_scores_record_ratio(
            annotate_scores_standard(scores, category, legacy=True),
            category
        )


@method_decorator(cache_page(60), name='list')
@filters.extend_schema_with_filters
class RecordListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_fields = (
        filters.CategoryFilter(),
        filters.LapModeFilter(required=False),
    )

    def get_queryset(self):
        records = self.filter(models.Score.objects).order_by(
            'track', 'is_lap', 'value', 'date'
        ).distinct(
            'track', 'is_lap'
        )

        scores = models.Score.objects.filter(
            pk__in=Subquery(records.values('pk'))
        ).annotate(
            rank=Value(1),
            record_ratio=Value(1),
        ).order_by(
            'track', 'is_lap'
        )

        return annotate_scores_standard(
            scores,
            self.get_filter_value(filters.CategoryFilter),
            legacy=True
        )
