from rest_framework import generics

from timetrials import filters, models, serializers


class StandardLevelListView(generics.ListAPIView):
    queryset = models.StandardLevel.objects.order_by('value').filter(is_legacy=True)
    serializer_class = serializers.StandardLevelSerializer


@filters.extend_schema_with_filters
class StandardListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.StandardSerializer
    filter_fields = (
        filters.CategoryFilter(),
    )

    def get_queryset(self):
        return self.filter(
            models.Standard.objects.order_by(
                'track', 'is_lap', 'level', '-category'
            ).distinct(
                'track', 'is_lap', 'level'
            )
        )
