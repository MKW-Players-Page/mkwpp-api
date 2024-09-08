from rest_framework import generics

from timetrials import models, serializers


class RegionListView(generics.ListAPIView):
    queryset = models.Region.objects.all()
    serializer_class = serializers.RegionSerializer
