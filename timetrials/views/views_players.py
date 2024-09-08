from rest_framework import generics

from timetrials import models, serializers


class PlayerListView(generics.ListAPIView):
    queryset = models.Player.objects.order_by('name')
    serializer_class = serializers.PlayerBasicSerializer


class PlayerRetrieveView(generics.RetrieveAPIView):
    queryset = models.Player.objects.all()
    serializer_class = serializers.PlayerSerializer
