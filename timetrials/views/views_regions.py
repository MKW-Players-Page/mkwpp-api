from rest_framework import generics

from timetrials import models, serializers


class RegionListView(generics.ListAPIView):
    queryset = models.Region.objects.order_by('id')
    serializer_class = serializers.RegionSerializer
