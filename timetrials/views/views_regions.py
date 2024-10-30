from django.db.models import F, Window
from django.db.models.functions import Rank

from rest_framework import generics

from timetrials import filters, models, serializers


class RegionListView(generics.ListAPIView):
    queryset = models.Region.objects.order_by('id')
    serializer_class = serializers.RegionSerializer


@filters.extend_schema_with_filters
class RegionStatsListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.RegionStatsSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
        filters.LapModeFilter(allow_overall=True),
        filters.RegionTypeFilter(field_name='region__type'),
        filters.RegionStatsTopScoreCountFilter(),
    )

    def get_queryset(self):
        score_count = models.Track.objects.count()
        if self.get_filter_value(filters.LapModeFilter) is None:
            score_count = score_count * 2

        return self.filter(models.RegionStats.objects.all()).filter(
            participation_count=score_count
        ).annotate(
            average_rank=(F('total_rank') / F('score_count')),
            rank=Window(Rank(), order_by='average_rank')
        )
