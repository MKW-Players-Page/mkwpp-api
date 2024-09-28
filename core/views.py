from datetime import timedelta

from django.core import signing
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions, generics, permissions, serializers, status, views
from rest_framework.response import Response
from rest_framework.authtoken.serializers import AuthTokenSerializer

from drf_spectacular.utils import extend_schema, OpenApiResponse

from knox.auth import TokenAuthentication
from knox.views import LoginView, LogoutView

from core.models import User


ACCOUNT_VERIFICATION_SALT = 'account_verification'
MAX_TOKEN_AGE = int(timedelta(days=2).total_seconds())


class AuthSerializer(AuthTokenSerializer):
    expiry = serializers.CharField(read_only=True)


@extend_schema(responses={
    200: OpenApiResponse(AuthSerializer),
    400: OpenApiResponse(description=_("Bad request")),
    401: OpenApiResponse(description=_("Unauthorized")),
    403: OpenApiResponse(description=_("Forbidden")),
})
class CoreLoginView(LoginView):
    serializer_class = AuthSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user = serializer.validated_data['user']

        if not request.user.is_verified:
            return Response({'non_field_errors': [
                _("Please activate your account before logging in."),
            ]}, status=status.HTTP_401_UNAUTHORIZED)

        return super().post(request, format)


@extend_schema(request=None, responses={
    200: OpenApiResponse(description=_("User was logged out successfully.")),
    401: OpenApiResponse(description=_("User is not authenticated.")),
})
class CoreLogoutView(LogoutView):
    pass


class UserSerializer(serializers.ModelSerializer):
    player = serializers.SerializerMethodField(read_only=True)

    def get_player(self, user: User) -> int:
        return user.player.id if hasattr(user, 'player') else 0

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'player']
        extra_kwargs = {
            'password': {'write_only': True},
        }


@extend_schema(responses={
    201: OpenApiResponse(description=_("User account was successfully created.")),
    400: OpenApiResponse(description=_("Invalid credentials were provided.")),
})
class CreateUserView(views.APIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create_user(self, request) -> User:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def get_message_context(self, user, token):
        return {
            'user': user,
            'token': token,
            'frontend_url': settings.FRONTEND_URL,
        }

    def post(self, request, *args, **kwargs):
        user = self.create_user(request)
        token = signing.dumps(obj=user.get_username(), salt=ACCOUNT_VERIFICATION_SALT)

        context = self.get_message_context(user, token)
        message = render_to_string('core/emails/account_verification.txt', context)

        try:
            user.email_user("Activate your account", message)

        except Exception:
            pass

        return Response(status=status.HTTP_201_CREATED)


class VerificationTokenSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)


@extend_schema(responses={
    204: OpenApiResponse(description=_("User account was successfully verified.")),
    400: OpenApiResponse(description=_("Token is invalid, has expired, or was already used.")),
})
class VerifyUserView(views.APIView):
    BAD_TOKEN_MESSAGE = _("This account verification token is not valid.")
    EXPIRED_TOKEN_MESSAGE = _("This validation token has expired! Please register once more.")
    ALREADY_VERIFIED_MESSAGE = _("This user account has already been verified!")

    serializer_class = VerificationTokenSerializer

    def validate_token(self, token):
        try:
            username = signing.loads(token, salt=ACCOUNT_VERIFICATION_SALT, max_age=MAX_TOKEN_AGE)
            return username

        except signing.SignatureExpired:
            raise exceptions.ValidationError(self.EXPIRED_TOKEN_MESSAGE, code='expired_token')

        except signing.BadSignature:
            raise exceptions.ValidationError(self.BAD_TOKEN_MESSAGE, code='bad_token')

    def get_user(self, username):
        try:
            user = User.objects.get(username=username)
            if user.is_verified:
                raise exceptions.ValidationError(self.ALREADY_VERIFIED_MESSAGE,
                                                 code='already_verified')

            return user

        except User.DoesNotExist:
            raise exceptions.ValidationError(self.BAD_TOKEN_MESSAGE, code='bad_token')

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = self.validate_token(request.data['token'])
        user = self.get_user(username)
        user.is_verified = True
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={
    200: OpenApiResponse(UserSerializer),
    401: OpenApiResponse(description=_("User is not authenticated.")),
})
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
