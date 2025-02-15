from datetime import timedelta

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse

from rest_framework import status
from rest_framework.response import Response

from core import serializers
from core.models import User
from core.views.generics import TokenGeneratorView, TokenVerifiedView


TOKEN_SALT = 'account_verification'
TOKEN_MAX_AGE = timedelta(days=2)


@extend_schema(responses={
    204: OpenApiResponse(description=_("User account was successfully created.")),
    400: OpenApiResponse(description=_("Invalid credentials were provided.")),
})
class CreateUserView(TokenGeneratorView):
    serializer_class = serializers.UserSerializer

    token_salt = TOKEN_SALT
    token_max_age = TOKEN_MAX_AGE

    email_template = 'core/emails/account_verification.txt'
    email_subject = _("Activate your account")

    def get_user(self) -> User:
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


@extend_schema(responses={
    204: OpenApiResponse(description=_("User account was successfully verified.")),
    401: OpenApiResponse(description=_("Token is invalid, has expired, or was already used.")),
})
class VerifyUserView(TokenVerifiedView):
    serializer_class = serializers.TokenSerializer

    token_salt = TOKEN_SALT
    token_max_age = TOKEN_MAX_AGE

    def on_success(self, user, data):
        user.is_verified = True
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
