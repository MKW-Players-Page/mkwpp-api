from django.db.models import QuerySet, Window
from django.db.models.functions import Rank

from rest_framework import generics

from timetrials import filters, models, serializers


class PlayerListView(generics.ListAPIView):
    queryset = models.Player.objects.order_by('name')
    serializer_class = serializers.PlayerBasicSerializer


class PlayerRetrieveView(generics.RetrieveAPIView):
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer


class PlayerStatsListView(generics.ListAPIView):
    queryset = models.PlayerStats.objects.none()
    serializer_class = serializers.PlayerStats
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.PlayerStatsFilter
    is_lap_as_null_bool = True
    do_not_expand_category = True

    def get_queryset(self):
        score_count = models.Track.objects.count()
        if 'is_lap' not in self.request.query_params:
            score_count = score_count * 2

        region = models.Region.objects.filter(
            code__iexact=self.request.query_params.get('region', None)
        ).first()

        if not region:
            region = models.Region.objects.filter(type=models.RegionTypeChoices.WORLD).first()

        return models.PlayerStats.objects.filter(score_count=score_count, region=region)

    def post_filter_queryset(self, queryset: QuerySet):
        return queryset.annotate(
            rank=Window(Rank(), order_by=queryset.query.order_by[0])
        )


class PlayerStatsRetrieveView(generics.ListAPIView):
    queryset = models.PlayerStats.objects.none()
    serializer_class = serializers.PlayerStats
    filter_backends = (filters.TimeTrialsFilterBackend,)
    filterset_class = filters.CategoryFilter
    is_lap_as_null_bool = True
    do_not_expand_category = True

    def get_queryset(self):
        region = models.Region.objects.filter(
            code__iexact=self.request.query_params.get('region', None)
        ).first()

        if not region:
            region = models.Region.objects.filter(type=models.RegionTypeChoices.WORLD).first()

        return models.PlayerStats.objects.filter(
            player=self.kwargs['pk'],
            region=region,
        ).annotate(rank=Window(Rank(), order_by='total_score'))
