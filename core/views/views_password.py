from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse

from knox.auth import TokenAuthentication

from rest_framework import permissions, status, views
from rest_framework.response import Response

from core import serializers
from core.models import User
from core.views.generics import TokenGeneratorView, TokenVerifiedView


TOKEN_SALT = 'password_reset'
TOKEN_MAX_AGE = timedelta(minutes=15)


@extend_schema(responses={
    204: OpenApiResponse(description=_("Password was changed successfully.")),
    400: OpenApiResponse(description=_(
        "Request is malformed, invalid credentials were provided, or new password is invalid."
    )),
    401: OpenApiResponse(description=_("User is not authenticated.")),
})
class PasswordChangeView(views.APIView):
    serializer_class = serializers.PasswordChangeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={
    204: OpenApiResponse(description=_("Request was processed successfully.")),
})
class PasswordResetRequestView(TokenGeneratorView):
    serializer_class = serializers.PasswordResetRequestSerializer

    token_salt = TOKEN_SALT
    token_max_age = TOKEN_MAX_AGE

    email_template = 'core/emails/password_reset.txt'
    email_subject = _("Reset password")

    def get_user(self) -> User:
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        return User.objects.filter(email__iexact=serializer.validated_data['email']).first()


@extend_schema(responses={
    204: OpenApiResponse(description=_("Request was processed successfully.")),
    401: OpenApiResponse(description=_("Provided token is invalid.")),
})
class PasswordResetView(TokenVerifiedView):
    serializer_class = serializers.PasswordResetSerializer

    token_salt = TOKEN_SALT
    token_max_age = TOKEN_MAX_AGE

    def on_success(self, user: User, data) -> Response:
        user.set_password(data['password'])
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
