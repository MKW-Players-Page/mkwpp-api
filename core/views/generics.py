from django.conf import settings
from django.core import signing
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, status, views
from rest_framework.response import Response

from core import serializers
from core.models import Token, User


class TokenGeneratorView(views.APIView):

    def get_user(self) -> User:
        raise NotImplementedError("View must implement 'get_user'.")

    def make_token(self, user: User) -> str:
        if not hasattr(self, 'token_salt') or not hasattr(self, 'token_max_age'):
            raise NotImplementedError("View must declare 'token_salt' and 'token_max_age'.")

        token = signing.dumps(obj=user.get_username(), salt=self.token_salt)
        expiry = timezone.now() + self.token_max_age

        Token.objects.create(
            token=token,
            salt=self.token_salt,
            expiry=expiry,
        )

        return token

    def get_message_context(self, user: User, token: str) -> dict:
        return {
            'user': user,
            'token': token,
            'frontend_url': settings.FRONTEND_URL,
        }

    def send_email(self, user: User, token: str):
        if not hasattr(self, 'email_template') or not hasattr(self, 'email_subject'):
            raise NotImplementedError("View must declare 'email_template' and 'email_subject'.")

        context = self.get_message_context(user, token)
        message = render_to_string(self.email_template, context, self.request)

        user.email_user(self.email_subject, message)

    def post(self, request, *args, **kwargs):
        user = self.get_user()
        if not user:
            return Response(status=status.HTTP_204_NO_CONTENT)

        token = self.make_token(user)

        self.send_email(user, token)

        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenVerifiedView(views.APIView):
    NO_TOKEN_MESSAGE = _("No token was provided.")
    BAD_TOKEN_MESSAGE = _("This token is not valid.")
    EXPIRED_TOKEN_MESSAGE = _("This token has expired.")
    USED_TOKEN_MESSAGE = _("This token has already been used.")

    serializer_class = serializers.TokenSerializer

    verify_only = False

    def get_token(self, data) -> str:
        return data['token']

    def validate_token(self, token: str) -> str:
        if not hasattr(self, 'token_salt') or not hasattr(self, 'token_max_age'):
            raise NotImplementedError("View must declare 'token_salt' and 'token_max_age'.")

        try:
            username = signing.loads(token, salt=self.token_salt, max_age=self.token_max_age)

        except signing.SignatureExpired:
            raise exceptions.AuthenticationFailed(self.EXPIRED_TOKEN_MESSAGE, code='expired_token')

        except signing.BadSignature:
            raise exceptions.AuthenticationFailed(self.BAD_TOKEN_MESSAGE, code='bad_token')

        # NOTE: This check is not atomic, so it is possible for multiple requests happening in quick
        # succession to all pass this check. This is not really a problem for the current use cases,
        # but this must be kept in mind when implementing new features using this generic view.
        try:
            saved_token = Token.objects.get(token=token, salt=self.token_salt)
            if saved_token.used:
                raise exceptions.AuthenticationFailed(self.USED_TOKEN_MESSAGE)

            if not self.verify_only:
                saved_token.used = True
                saved_token.save()

        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed(self.BAD_TOKEN_MESSAGE)

        return username

    def get_user(self, username) -> User:
        try:
            return User.objects.get(username=username)

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(self.BAD_TOKEN_MESSAGE, code='bad_token')

    def on_success(self, user: User, data) -> Response:
        raise NotImplementedError("View must implement 'on_success'.")

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = self.get_token(serializer.validated_data)
        username = self.validate_token(token)
        user = self.get_user(username)

        if self.verify_only:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return self.on_success(user, serializer.validated_data)
