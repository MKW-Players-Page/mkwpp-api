from django_filters import rest_framework as filters

from rest_framework import generics

from timetrials import models, serializers


class PlayerScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ['category']

    def get_queryset(self):
        return models.Score.objects.filter(player=self.kwargs['pk'])


class TrackScoreListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ['category', 'is_lap']

    def get_queryset(self):
        return models.Score.objects.filter(track=self.kwargs['pk']).order_by('value', 'date')


class RecordListView(generics.ListAPIView):
    queryset = models.Score.objects.none()
    serializer_class = serializers.ScoreWithPlayerSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ['category']

    def get_queryset(self):
        return (
            models.Score.objects
            .order_by('track', 'is_lap', 'value', 'date')
            .distinct('track', 'is_lap')
        )
