from rest_framework import generics

from timetrials import filters, models, serializers
from timetrials.models.sitechamp import SiteChampion

@filters.extend_schema_with_filters
class SiteChampListView(filters.FilterMixin, generics.ListAPIView):
    queryset = SiteChampion.objects.all().order_by('date_became_champion')
    serializer_class = serializers.SiteChampionSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
    )
