from django.urls import path

from timetrials import views


urlpatterns = [
    path('regions/', views.RegionListView.as_view(), name='region-list'),
    path('standards/', views.StandardListView.as_view(), name='standard-list'),
    path('cups/', views.TrackCupListView.as_view(), name='trackcup-list'),
    path('tracks/', views.TrackListView.as_view(), name='track-list'),
    path('tracks/<int:pk>/scores/', views.TrackScoreListView.as_view(), name='track-score-list'),
    path('players/', views.PlayerListView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PlayerRetrieveView.as_view(), name='player-details'),
    path('players/<int:pk>/scores/', views.PlayerScoreListView.as_view(), name='player-score-list'),
    path('records/', views.RecordListView.as_view(), name='record-list'),
]
