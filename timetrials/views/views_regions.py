from django.db.models import F, FloatField, Value, Window
from django.db.models.functions import Cast, Rank

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
        max_score_count = models.Track.objects.count()
        if self.get_filter_value(filters.LapModeFilter) is None:
            max_score_count *= 2

        top_score_count = self.get_filter_value(filters.RegionStatsTopScoreCountFilter)

        score_count = F('score_count') if top_score_count == 0 else Value(max_score_count)

        return self.filter(models.RegionStats.objects.all()).filter(
            score_count__gt=0
        ).annotate(
            average_rank=Cast(F('total_rank'), output_field=FloatField()) / score_count,
            rank=Window(Rank(), order_by='average_rank')
        )
