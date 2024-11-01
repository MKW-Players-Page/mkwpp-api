from django.db.models import (
  ExpressionWrapper, F, IntegerField, OuterRef, Q, Subquery, Value, Window
)
from django.db.models.functions import Rank
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, views
from rest_framework.response import Response

from timetrials import filters, models, serializers
from timetrials.models.regions import RegionTypeChoices
from timetrials.models.scores import ScoreSubmissionStatus


class PlayerListView(generics.ListAPIView):
    queryset = models.Player.objects.order_by('name')
    serializer_class = serializers.PlayerBasicSerializer


class PlayerRetrieveView(generics.RetrieveAPIView):
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer


@filters.extend_schema_with_filters
class PlayerStatsListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerStatsSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
        filters.LapModeFilter(allow_overall=True),
        filters.RegionFilter(expand=False, ranked_only=True),
        filters.MetricOrderingFilter(),
    )

    def get_queryset(self):
        score_count = models.Track.objects.count()
        if self.get_filter_value(filters.LapModeFilter) is None:
            score_count = score_count * 2

        return self.filter(models.PlayerStats.objects.all()).filter(
            score_count=score_count
        ).annotate(
            rank=Window(Rank(), order_by=self.get_filter_value(filters.MetricOrderingFilter))
        )


@filters.extend_schema_with_filters
class PlayerStatsRetrieveView(filters.FilterMixin, generics.RetrieveAPIView):
    serializer_class = serializers.PlayerStatsSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
        filters.LapModeFilter(allow_overall=True),
        filters.RegionFilter(expand=False, ranked_only=True),
    )

    def get_queryset(self):
        # Temporarily hardcode rank to 1
        return self.filter(models.PlayerStats.objects.all()).annotate(rank=Value(1))

    def get_object(self):
        return get_object_or_404(self.get_queryset(), player=self.kwargs['pk'])


@filters.extend_schema_with_filters
class PlayerMatchupRetrieveView(filters.FilterMixin, views.APIView):
    serializer_class = serializers.PlayerMatchupSerializer
    filter_fields = (
        filters.CategoryFilter(),
        filters.LapModeFilter(allow_overall=True, auto=False)
    )

    def get_player(self, index):
        player = models.Player.objects.filter(pk=self.kwargs[f'pk{index}']).first()
        if not player:
            raise Http404("Player %d not found" % index)

        player.player_scores = self.filter(models.Score.objects.all()).filter(
            player=player,
            status=ScoreSubmissionStatus.ACCEPTED,
        ).distinct(
            'track', 'is_lap'
        ).order_by(
            'track', 'is_lap', 'value'
        )

        lap_mode = self.get_filter_value(filters.LapModeFilter)
        if lap_mode is not None:
            player.player_scores = player.player_scores.filter(is_lap=lap_mode)

        world = models.Region.objects.filter(type=RegionTypeChoices.WORLD).first()

        player.player_stats = models.PlayerStats.objects.filter(
            player=player,
            region=world,
            is_lap=lap_mode,
            category=self.get_filter_value(filters.CategoryFilter),
        ).first()

        return player

    def annotate_differences(self, p1, p2):
        def annotate(base, other):
            base.player_scores = base.player_scores.annotate(
                difference=Subquery(
                    models.Score.objects.filter(
                        pk__in=other.player_scores.values('pk'),
                        track=OuterRef('track'),
                        is_lap=OuterRef('is_lap'),
                    ).annotate(
                        difference=ExpressionWrapper(
                            OuterRef('value') - F('value'),
                            output_field=IntegerField(),
                        )
                    ).values('difference')
                ),
            )

        annotate(p1, p2)
        annotate(p2, p1)

        def total_wins(player):
            return player.player_scores.filter(
                Q(difference__lt=0) | Q(difference__isnull=True)
            ).count()

        p1.total_wins = total_wins(p1)
        p2.total_wins = total_wins(p2)

        def total_ties(player):
            return player.player_scores.filter(difference=0).count()

        p1.total_ties = total_ties(p1)
        p2.total_ties = total_ties(p2)

    def get_response(self, p1, p2):
        instance = {
            'p1': p1,
            'p2': p2,
        }
        serializer = self.serializer_class()
        return serializer.to_representation(instance)

    def get(self, request, *args, **kwargs):
        if kwargs['pk1'] == kwargs['pk2']:
            return Response(
                {'non_field_errors': ["Cannot compare against the same player"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        p1 = self.get_player(1)
        p2 = self.get_player(2)

        self.annotate_differences(p1, p2)

        return Response(self.get_response(p1, p2), status=status.HTTP_200_OK)


@filters.extend_schema_with_filters
class PlayerAwardListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerAwardSerializer
    filter_fields = (
        filters.PlayerAwardTypeFilter(),
    )

    def get_queryset(self):
        return self.filter(models.PlayerAward.objects.all()).order_by('-date')
