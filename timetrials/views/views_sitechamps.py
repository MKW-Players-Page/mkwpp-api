from rest_framework import generics

from timetrials import filters, models, serializers


@filters.extend_schema_with_filters
class SiteChampListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.SiteChampionSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
    )

    def get_queryset(self):
        return self.filter(models.SiteChampion.objects.all()).order_by('date_instated')
