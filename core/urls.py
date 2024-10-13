from django.urls import path

from core import views


urlpatterns = [
    path('login/', views.CoreLoginView.as_view(), name='login'),
    path('logout/', views.CoreLogoutView.as_view(), name='logout'),
    path('signup/', views.CreateUserView.as_view(), name='create-user'),
    path('verify/', views.VerifyUserView.as_view(), name='verify-user'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('blog/latest/', views.LatestBlogPostListView.as_view(), name='blog-latest'),
    path('blog/<int:pk>/', views.BlogPostRetrieveView.as_view(), name='blog-post'),
]
