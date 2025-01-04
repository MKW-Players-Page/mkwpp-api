from timetrials.views.views_players import (
    PlayerAwardListView, PlayerListView, PlayerRetrieveView, PlayerStatsListView,
    PlayerStatsRetrieveView, PlayerUpdateView
)
from timetrials.views.views_regions import RegionListView, RegionStatsListView
from timetrials.views.views_scores import (
    LatestRecordListView, LatestScoreListView, PlayerScoreListView, RecordListView,
    TrackScoreListView, TrackTopsListView
)
from timetrials.views.views_sitechamps import SiteChampListView
from timetrials.views.views_standards import StandardListView
from timetrials.views.views_submissions import (
    EditScoreSubmissionCreateView,
    EditScoreSubmissionDestroyView,
    EditScoreSubmissionListView,
    PlayerSubmitterCreateView,
    PlayerSubmitterDestroyView,
    PlayerSubmitteeListView,
    PlayerSubmitterListView,
    ScoreSubmissionCreateView,
    ScoreSubmissionDestroyView,
    ScoreSubmissionListView,
)
from timetrials.views.views_tracks import TrackCupListView, TrackListView
