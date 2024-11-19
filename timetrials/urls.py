from django.urls import path

from timetrials import views


urlpatterns = [
    path('regions/', views.RegionListView.as_view(), name='region-list'),
    path('regions/rankings/', views.RegionStatsListView.as_view(), name='region-stats-list'),
    path('standards/', views.StandardListView.as_view(), name='standard-list'),
    path('cups/', views.TrackCupListView.as_view(), name='trackcup-list'),
    path('tracks/', views.TrackListView.as_view(), name='track-list'),
    path('tracks/<int:pk>/scores/', views.TrackScoreListView.as_view(), name='track-score-list'),
    path('tracks/<int:pk>/tops/', views.TrackTopsListView.as_view(), name='track-tops-list'),
    path('scores/latest/', views.LatestScoreListView.as_view(), name='latest-score-list'),
    path('records/', views.RecordListView.as_view(), name='record-list'),
    path('players/', views.PlayerListView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PlayerRetrieveView.as_view(), name='player-details'),
    path('players/<int:pk>/scores/', views.PlayerScoreListView.as_view(), name='player-score-list'),
    path('players/<int:pk>/stats/', views.PlayerStatsRetrieveView.as_view(), name='player-stats'),
    path('profile/', views.PlayerUpdateView.as_view(), name='player-update'),
    path('rankings/', views.PlayerStatsListView.as_view(), name='player-stats-list'),
    path('awards/', views.PlayerAwardListView.as_view(), name='award-list'),
    path('champions/', views.SiteChampListView.as_view(), name='champion-list'),
    path('submissions/', views.UserSubmissionListView.as_view(), name='user-submission-list'),
    path('submissions/create/', views.ScoreSubmissionCreateView.as_view(),
         name='submission-create'),
]
