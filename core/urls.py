from django.urls import path

from core import views


urlpatterns = [
    path('login/', views.CoreLoginView.as_view(), name='login'),
    path('logout/', views.CoreLogoutView.as_view(), name='logout'),
    path('user/', views.CurrentUserView.as_view(), name='current-user'),
]
