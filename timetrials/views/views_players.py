from django.db.models import Value, Window
from django.db.models.functions import Rank
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from knox.auth import TokenAuthentication

from timetrials import filters, models, serializers


@filters.extend_schema_with_filters
class PlayerListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerBasicSerializer
    filter_fields = (
        filters.OffsetFilter(),
        filters.LimitFilter(),
    )

    def get_queryset(self):
        return self.limit(models.Player.objects.order_by('name'))


class PlayerRetrieveView(generics.RetrieveAPIView):
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer


class PlayerUpdateView(generics.UpdateAPIView):
    serializer_class = serializers.PlayerUpdateSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'player'):
            raise ValidationError(_("User has no associated player profile."))
        return user.player


@filters.extend_schema_with_filters
class PlayerStatsListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerStatsSerializer
    filter_fields = (
        filters.CategoryFilter(expand=False),
        filters.LapModeFilter(allow_overall=True),
        filters.RegionFilter(expand=False, ranked_only=True),
        filters.MetricOrderingFilter(),
        filters.OffsetFilter(),
        filters.LimitFilter(),
    )

    def get_queryset(self):
        score_count = models.Track.objects.count()
        if self.get_filter_value(filters.LapModeFilter) is None:
            score_count = score_count * 2

        return self.limit(
            self.filter(models.PlayerStats.objects.all()).filter(
                score_count=score_count
            ).annotate(
                rank=Window(Rank(), order_by=self.get_filter_value(filters.MetricOrderingFilter))
            )
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
class PlayerAwardListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.PlayerAwardSerializer
    filter_fields = (
        filters.PlayerAwardTypeFilter(),
    )

    def get_queryset(self):
        return self.filter(models.PlayerAward.objects.all()).order_by('-date')
