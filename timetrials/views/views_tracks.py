from rest_framework import generics

from timetrials import models, serializers


class TrackListView(generics.ListAPIView):
    queryset = models.Track.objects.order_by('id')
    serializer_class = serializers.TrackSerializer


class TrackCupListView(generics.ListAPIView):
    queryset = models.TrackCup.objects.order_by('id')
    serializer_class = serializers.TrackCupSerializer
