from django.contrib.auth.password_validation import validate_password

from rest_framework import generics, permissions, serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from drf_spectacular.utils import extend_schema

from knox.auth import TokenAuthentication
from knox.views import LoginView, LogoutView

from core.models import User


class AuthSerializer(AuthTokenSerializer):
    expiry = serializers.CharField(read_only=True)


@extend_schema(operation_id='login')
class CoreLoginView(LoginView):
    serializer_class = AuthSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user = serializer.validated_data['user']
        return super().post(request, format)


@extend_schema(operation_id='logout')
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


@extend_schema(operation_id='create_user')
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


@extend_schema(operation_id='current_user')
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
