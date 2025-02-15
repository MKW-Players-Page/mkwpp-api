from rest_framework import generics

from core import serializers
from core.models import BlogPost


class BlogPostListView(generics.ListAPIView):
    serializer_class = serializers.BlogPostSummarySerializer
    queryset = BlogPost.objects.filter(is_published=True).order_by('-published_at')


class LatestBlogPostListView(generics.ListAPIView):
    serializer_class = serializers.BlogPostSerializer
    queryset = BlogPost.objects.filter(is_published=True).order_by('-published_at')[:5]


class BlogPostRetrieveView(generics.RetrieveAPIView):
    serializer_class = serializers.BlogPostSerializer
    queryset = BlogPost.objects.filter(is_published=True)
