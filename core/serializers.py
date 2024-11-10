from django.contrib.auth.password_validation import validate_password

from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers
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


class VerificationTokenSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)


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
