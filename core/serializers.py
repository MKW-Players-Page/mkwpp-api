from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema_field

from rest_framework import exceptions, serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from core.models import BlogPost, User


# Fields

@extend_schema_field(serializers.FloatField())
class TimestampField(serializers.Field):

    def to_representation(self, value):
        return value.timestamp()


# User

class AuthSerializer(AuthTokenSerializer):
    expiry = serializers.CharField(read_only=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context.get('request').user
        if not user.check_password(value):
            raise exceptions.ValidationError(_("Current password does not match."))
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetSerializer(TokenSerializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value


class UserSerializer(serializers.ModelSerializer):
    player = serializers.SerializerMethodField(read_only=True)

    def get_player(self, user: User) -> int:
        return user.player.id if user.player is not None else 0

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


# Blog posts

class BlogPostSummarySerializer(serializers.ModelSerializer):
    author = UserSerializer()
    published_at = TimestampField()

    class Meta:
        model = BlogPost
        fields = ['id', 'author', 'title', 'published_at']


class BlogPostSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    published_at = TimestampField()

    class Meta:
        model = BlogPost
        fields = ['id', 'author', 'title', 'content', 'published_at']
