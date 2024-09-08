from django_filters import rest_framework as filters

from rest_framework import generics

from timetrials import models, serializers


class StandardListView(generics.ListAPIView):
    queryset = models.StandardLevel.objects.order_by('is_legacy', 'value')
    serializer_class = serializers.StandardLevelSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ['is_legacy']
