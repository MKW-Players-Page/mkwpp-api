from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, OpenApiResponse

from knox.auth import TokenAuthentication
from knox.views import LoginView, LogoutView
from rest_framework.authtoken.serializers import AuthTokenSerializer

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from core import serializers


@extend_schema(responses={
    200: OpenApiResponse(serializers.AuthSerializer),
    400: OpenApiResponse(description=_("Bad request")),
    401: OpenApiResponse(description=_("Unauthorized")),
    403: OpenApiResponse(description=_("Forbidden")),
})
class CoreLoginView(LoginView):
    serializer_class = serializers.AuthSerializer
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
    204: OpenApiResponse(description=_("User was logged out successfully.")),
    401: OpenApiResponse(description=_("User is not authenticated.")),
})
class CoreLogoutView(LogoutView):
    pass


@extend_schema(responses={
    200: OpenApiResponse(serializers.UserSerializer),
    401: OpenApiResponse(description=_("User is not authenticated.")),
})
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = serializers.UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
