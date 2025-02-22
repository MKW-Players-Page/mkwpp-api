from django.urls import path

from core import views


urlpatterns = [
    path('login/', views.CoreLoginView.as_view(), name='login'),
    path('logout/', views.CoreLogoutView.as_view(), name='logout'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    path('password/reset/request/', views.PasswordResetRequestView.as_view(),
         name='password-reset-request'),
    path('password/reset/verify/', views.PasswordResetVerifyView.as_view(),
         name='password-reset-verify'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password-reset'),
    path('signup/', views.CreateUserView.as_view(), name='create-user'),
    path('verify/', views.VerifyUserView.as_view(), name='verify-user'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
    path('profile/claim', views.ProfileClaimView.as_view(), name='profile-claim'),
    path('profile/create', views.ProfileCreateView.as_view(), name='profile-create'),
    path('blog/', views.BlogPostListView.as_view(), name='blog-list'),
    path('blog/latest/', views.LatestBlogPostListView.as_view(), name='blog-latest'),
    path('blog/<int:pk>/', views.BlogPostRetrieveView.as_view(), name='blog-post'),
]
