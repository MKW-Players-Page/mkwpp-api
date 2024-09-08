from django.db.models import QuerySet, Subquery

import django_filters
from django_filters import rest_framework as filters

from rest_framework import generics

from timetrials import models, serializers
from timetrials.models.categories import category_filter


class PostFilterBackend(filters.DjangoFilterBackend):
    """Allow filtering queryset after filterset."""

    def filter_queryset(self, request, queryset, view):
        qs = super().filter_queryset(request, queryset, view)

        post_filter_queryset = getattr(view, 'post_filter_queryset', None)
        if post_filter_queryset:
            return post_filter_queryset(qs)

        return qs


class CategoryFilter(django_filters.FilterSet):
    """Filter by category by properly following fallthrough rules as well as by course or lap."""
    category = django_filters.CharFilter(method=category_filter)

    class Meta:
        model = models.Score
        fields = ['category', 'is_lap']


class PlayerScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CategoryFilter

    def get_queryset(self):
        return (
            models.Score.objects
            .filter(player=self.kwargs['pk'])
            .order_by('track', 'is_lap', 'value')
            .distinct('track', 'is_lap')
        )


class TrackScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (PostFilterBackend,)
    filterset_class = CategoryFilter

    def get_queryset(self):
        return models.Score.objects.filter(track=self.kwargs['pk'])

    def post_filter_queryset(self, queryset: QuerySet):
        return (
            models.Score.objects
            .filter(pk__in=Subquery(
                queryset.order_by('player', 'value').distinct('player').values('pk')
            ))
            .order_by('value', 'date')
        )


class RecordListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CategoryFilter

    def get_queryset(self):
        return (
            models.Score.objects
            .order_by('track', 'is_lap', 'value', 'date')
            .distinct('track', 'is_lap')
        )
