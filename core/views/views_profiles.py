from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse

from knox.auth import TokenAuthentication

from rest_framework import exceptions, generics, permissions, status, views
from rest_framework.response import Response

from core import serializers


class ProfileCreateView(generics.CreateAPIView):
    serializer_class = serializers.ProfileCreateSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        if request.user.player:
            raise exceptions.ValidationError(_("Account already associated with a profile."))

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        self.request.user.player = serializer.save()
        self.request.user.save()


@extend_schema(responses={
    204: OpenApiResponse(description=_("Profile was linked successfully.")),
})
class ProfileClaimView(views.APIView):
    serializer_class = serializers.ProfileClaimSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.player:
            raise exceptions.ValidationError(_("Account already associated with a profile."))

        player = serializer.validated_data['player']
        if hasattr(player, 'user'):
            raise exceptions.ValidationError(_("Profile already associated with an account."))

        request.user.player = player
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
