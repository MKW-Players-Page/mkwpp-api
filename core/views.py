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
    class Meta:
        model = User
        fields = ['username', 'email', 'player']


@extend_schema(operation_id='current_user')
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
