from rest_framework import generics, permissions

from knox.auth import TokenAuthentication

from timetrials import filters, models, serializers


class ScoreSubmissionCreateView(generics.CreateAPIView):
    serializer_class = serializers.ScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        return serializer.save(submitted_by=self.request.user)


@filters.extend_schema_with_filters
class ScoreSubmissionListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.ScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = (
        filters.ScoreSubmissionStatusFilter(required=False),
    )

    def get_queryset(self):
        return self.filter(models.ScoreSubmission.objects.filter(submitted_by=self.request.user))


class ScoreSubmissionDestroyView(generics.DestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return models.ScoreSubmission.objects.filter(
            submitted_by=self.request.user,
            status=models.ScoreSubmissionStatus.PENDING,
        )


class EditScoreSubmissionCreateView(generics.CreateAPIView):
    serializer_class = serializers.EditScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        print(serializer.validated_data)
        return serializer.save(submitted_by=self.request.user)


@filters.extend_schema_with_filters
class EditScoreSubmissionListView(filters.FilterMixin, generics.ListAPIView):
    serializer_class = serializers.EditScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = (
        filters.ScoreSubmissionStatusFilter(required=False),
    )

    def get_queryset(self):
        return self.filter(models.EditScoreSubmission.objects.filter(
            submitted_by=self.request.user
        ))


class EditScoreSubmissionDestroyView(generics.DestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return models.EditScoreSubmission.objects.filter(
            submitted_by=self.request.user,
            status=models.ScoreSubmissionStatus.PENDING,
        )
