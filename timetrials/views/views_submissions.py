from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import generics, permissions, status, views
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from knox.auth import TokenAuthentication

from core.models import User

from timetrials import filters, models, serializers


def can_create_submission(user, player):
    if hasattr(user, 'player') and user.player == player:
        return True

    return models.PlayerSubmitter.objects.filter(player=player, submitter=user).exists()


class ScoreSubmissionCreateView(generics.CreateAPIView):
    serializer_class = serializers.ScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        if not can_create_submission(self.request.user, serializer.validated_data['player']):
            raise ValidationError(_("You may not create submissions for this player."))

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
        if hasattr(self.request.user, 'player'):
            queryset = models.ScoreSubmission.objects.filter(
                Q(player=self.request.user.player) | Q(submitted_by=self.request.user)
            )
        else:
            queryset = models.ScoreSubmission.objects.filter(submitted_by=self.request.user)

        return self.filter(queryset)


class ScoreSubmissionDestroyView(generics.DestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if hasattr(self.request.user, 'player'):
            queryset = models.ScoreSubmission.objects.filter(
                Q(player=self.request.user.player) | Q(submitted_by=self.request.user)
            )
        else:
            queryset = models.ScoreSubmission.objects.filter(submitted_by=self.request.user)

        return queryset.filter(status=models.ScoreSubmissionStatus.PENDING)


class EditScoreSubmissionCreateView(generics.CreateAPIView):
    serializer_class = serializers.EditScoreSubmissionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        if not can_create_submission(self.request.user, serializer.validated_data['score'].player):
            raise ValidationError(_("You may not create submissions for this player."))

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
        if hasattr(self.request.user, 'player'):
            queryset = models.EditScoreSubmission.objects.filter(
                Q(score__player=self.request.user.player) | Q(submitted_by=self.request.user)
            )
        else:
            queryset = models.EditScoreSubmission.objects.filter(submitted_by=self.request.user)

        return self.filter(queryset)


class EditScoreSubmissionDestroyView(generics.DestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if hasattr(self.request.user, 'player'):
            queryset = models.EditScoreSubmission.objects.filter(
                Q(score__player=self.request.user.player) | Q(submitted_by=self.request.user)
            )
        else:
            queryset = models.EditScoreSubmission.objects.filter(submitted_by=self.request.user)

        return queryset.filter(status=models.ScoreSubmissionStatus.PENDING)


class PlayerSubmitteeListView(generics.ListAPIView):
    serializer_class = serializers.PlayerSubmitteeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return models.PlayerSubmitter.objects.filter(submitter=self.request.user)


class PlayerSubmitterListView(generics.ListAPIView):
    serializer_class = serializers.PlayerSubmitterSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if not hasattr(self.request.user, 'player'):
            raise ValidationError(_("User has no associated player profile."))

        return models.PlayerSubmitter.objects.filter(player=self.request.user.player)


class PlayerSubmitterCreateView(views.APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'player'):
            raise ValidationError(_("User has no associated player profile."))

        submitter = User.objects.filter(id=self.kwargs['pk']).first()
        if submitter is None:
            raise ValidationError(_("No user with given ID."))
        if submitter.id == request.user.id:
            raise ValidationError(_("You may not assign yourself as your own submitter."))

        player = request.user.player
        if models.PlayerSubmitter.objects.filter(player=player, submitter=submitter).exists():
            raise ValidationError(_("The given user has already been assigned as a submitter."))

        models.PlayerSubmitter.objects.create(player=player, submitter=submitter)

        return Response(status=status.HTTP_201_CREATED)


class PlayerSubmitterDestroyView(views.APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        if not hasattr(request.user, 'player'):
            raise ValidationError(_("User has no associated player profile."))

        result = models.PlayerSubmitter.objects.filter(
            player=request.user.player,
            submitter_id=self.kwargs['pk'],
        ).delete()

        if result[0] == 0:
            raise ValidationError(_("The given user was not previously assigned as a submitter."))

        return Response(status=status.HTTP_204_NO_CONTENT)
