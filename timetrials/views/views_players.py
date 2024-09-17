from django.db.models import Value, Window
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404

from rest_framework import generics

from timetrials import filters, models, serializers


class PlayerListView(generics.ListAPIView):
    queryset = models.Player.objects.order_by('name')
    serializer_class = serializers.PlayerBasicSerializer


class PlayerRetrieveView(generics.RetrieveAPIView):
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer


@filters.extend_schema_with_filters
class PlayerStatsListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerStats
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
    serializer_class = serializers.PlayerStats
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
