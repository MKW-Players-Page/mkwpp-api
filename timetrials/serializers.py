from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers

from core.serializers import TimestampField

from timetrials import models, queries
from timetrials.models.categories import CategoryChoices
from timetrials.models.scores import ScoreSubmissionStatus
from timetrials.models.stats.region_stats import TopScoreCountChoices


# Custom fields

def map_enum_field(mapping: dict):
    reverse = {v: k for k, v in mapping.items()}

    @extend_schema_field(serializers.ChoiceField(choices=mapping.values()))
    class MappedEnumField(serializers.Field):

        def to_representation(self, value):
            return mapping.get(value, None)

        def to_internal_value(self, data):
            return reverse.get(data, None)

        @classmethod
        def values(cls):
            return mapping.values()

    return MappedEnumField


CategoryField = map_enum_field({
    CategoryChoices.NON_SHORTCUT: 'nonsc',
    CategoryChoices.SHORTCUT: 'sc',
    CategoryChoices.UNRESTRICTED: 'unres',
})


class MultiCategoryField(serializers.MultipleChoiceField):

    def __init__(self, **kwargs):
        kwargs = {'choices': CategoryChoices.choices, **kwargs}
        super().__init__(**kwargs)

    def to_representation(self, value):
        field = CategoryField()
        values = super().to_representation(value)
        return [field.to_representation(value) for value in values]

    def to_internal_value(self, data):
        field = CategoryField()
        values = super().to_internal_value(data)
        return [field.to_internal_value(value) for value in values]


ScoreSubmissionStatusField = map_enum_field({
    ScoreSubmissionStatus.PENDING: 'pending',
    ScoreSubmissionStatus.ACCEPTED: 'accepted',
    ScoreSubmissionStatus.REJECTED: 'rejected',
    ScoreSubmissionStatus.ON_HOLD: 'on_hold',
})

TopScoreCountField = map_enum_field({
    TopScoreCountChoices.ALL: 'all',
    TopScoreCountChoices.TOP_1: 'records',
    TopScoreCountChoices.TOP_3: 'top3',
    TopScoreCountChoices.TOP_5: 'top5',
    TopScoreCountChoices.TOP_10: 'top10',
})


# Regions

class RegionSerializer(serializers.ModelSerializer):
    player_count = serializers.SerializerMethodField()

    def get_player_count(self, region: models.Region) -> int:
        return queries.query_region_players(region).count()

    class Meta:
        model = models.Region
        fields = ['id', 'type', 'name', 'code', 'parent', 'is_ranked', 'player_count']


class RegionStatsSerializer(serializers.ModelSerializer):
    region = RegionSerializer()
    top_score_count = TopScoreCountField()
    category = CategoryField()
    rank = serializers.IntegerField()
    average_rank = serializers.SerializerMethodField()
    average_standard = serializers.SerializerMethodField()
    average_record_ratio = serializers.SerializerMethodField()

    def get_average_rank(self, stats: models.RegionStats) -> str:
        return f"{stats.total_rank/stats.effective_score_count:.08}"

    def get_average_standard(self, stats: models.RegionStats) -> str:
        return f"{stats.total_standard/stats.effective_score_count:.08}"

    def get_average_record_ratio(self, stats: models.RegionStats) -> str:
        return f"{stats.total_record_ratio/stats.effective_score_count:.08}"

    class Meta:
        model = models.RegionStats
        fields = [
            'region',
            'top_score_count',
            'category',
            'is_lap',
            'rank',
            'participation_count',
            'score_count',
            'total_score',
            'total_rank',
            'average_rank',
            'total_standard',
            'average_standard',
            'total_record_ratio',
            'average_record_ratio',
            'total_records',
        ]


# Tracks

class TrackSerializer(serializers.ModelSerializer):
    categories = MultiCategoryField()

    class Meta:
        model = models.Track
        fields = ['id', 'name', 'abbr', 'cup', 'categories']


class TrackCupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrackCup
        fields = ['id', 'name', 'code', 'tracks']


# Players

class PlayerBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Player
        fields = ['id', 'name', 'region', 'user', 'alias', 'joined_date', 'last_activity']


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Player
        fields = PlayerBasicSerializer.Meta.fields + ['bio']


class PlayerUpdateSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        return super().validate({
            key: None if isinstance(value, str) and len(value) == 0 else value
            for key, value in attrs.items()
        })

    class Meta:
        model = models.Player
        fields = ['alias', 'bio']


class PlayerStatsSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField()
    player = PlayerBasicSerializer()
    category = CategoryField()
    average_rank = serializers.SerializerMethodField()
    average_standard = serializers.SerializerMethodField()
    average_record_ratio = serializers.SerializerMethodField()

    def get_average_rank(self, stats: models.PlayerStats) -> str:
        return f"{stats.total_rank/stats.effective_score_count:.08}"

    def get_average_standard(self, stats: models.PlayerStats) -> str:
        return f"{stats.total_standard/stats.effective_score_count:.08}"

    def get_average_record_ratio(self, stats: models.PlayerStats) -> str:
        return f"{stats.total_record_ratio/stats.effective_score_count:.08}"

    class Meta:
        model = models.PlayerStats
        fields = [
            'rank',
            'player',
            'region',
            'category',
            'is_lap',
            'score_count',
            'total_score',
            'total_rank',
            'average_rank',
            'total_standard',
            'average_standard',
            'total_record_ratio',
            'average_record_ratio',
            'total_records',
            'leaderboard_points',
        ]


class PlayerAwardSerializer(serializers.ModelSerializer):
    player = PlayerBasicSerializer()

    class Meta:
        model = models.PlayerAward
        fields = ['id', 'player', 'type', 'date', 'description']


# Scores

class ScoreBasicSerializer(serializers.ModelSerializer):
    category = CategoryField()

    class Meta:
        model = models.Score
        fields = [
            'id',
            'value',
            'player',
            'track',
            'category',
            'is_lap',
            'date',
            'video_link',
            'ghost_link',
            'comment',
        ]


class RecentScoreSerializer(ScoreBasicSerializer):
    player = PlayerBasicSerializer()
    category = CategoryField()

    class Meta:
        model = models.Score
        fields = [
            'id',
            'value',
            'player',
            'track',
            'category',
            'is_lap',
            'date',
            'initial_rank',
            'video_link',
            'ghost_link',
            'comment',
        ]


class ScoreSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField()
    category = CategoryField()
    standard = serializers.IntegerField()
    record_ratio = serializers.FloatField()

    class Meta:
        model = models.Score
        fields = [
            'id',
            'rank',
            'value',
            'player',
            'track',
            'category',
            'is_lap',
            'standard',
            'record_ratio',
            'date',
            'video_link',
            'ghost_link',
            'comment',
        ]


class ScoreWithPlayerSerializer(ScoreSerializer):
    player = PlayerBasicSerializer()


class ScoreSubmissionSerializer(serializers.ModelSerializer):
    player = PlayerBasicSerializer(read_only=True)
    player_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Player.objects.all(),
        write_only=True,
        source='player'
    )
    category = CategoryField()
    status = ScoreSubmissionStatusField(read_only=True)

    class Meta:
        model = models.ScoreSubmission
        fields = [
            'id',
            'value',
            'player',
            'player_id',
            'track',
            'category',
            'is_lap',
            'date',
            'video_link',
            'ghost_link',
            'comment',
            'status',
            'submitted_by',
            'submitted_at',
            'submitter_note',
            'reviewed_by',
            'reviewed_at',
            'reviewer_note',
        ]
        extra_kwargs = {
            'submitted_by': {'read_only': True},
            'submitted_at': {'read_only': True},
            'reviewed_by': {'read_only': True},
            'reviewed_at': {'read_only': True},
            'reviewer_note': {'read_only': True},
        }


class EditScoreSubmissionSerializer(serializers.ModelSerializer):
    score = ScoreBasicSerializer(read_only=True)
    score_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Score.objects.all(),
        write_only=True,
        source='score'
    )
    status = ScoreSubmissionStatusField(read_only=True)

    def validate(self, attrs):
        attrs['video_link_edited'] = 'video_link' in attrs
        attrs['ghost_link_edited'] = 'ghost_link' in attrs
        attrs['comment_edited'] = 'comment' in attrs
        return super().validate(attrs)

    class Meta:
        model = models.EditScoreSubmission
        fields = [
            'id',
            'score',
            'score_id',
            'video_link_edited',
            'video_link',
            'ghost_link_edited',
            'ghost_link',
            'comment_edited',
            'comment',
            'status',
            'submitted_by',
            'submitted_at',
            'submitter_note',
            'reviewed_by',
            'reviewed_at',
            'reviewer_note',
        ]
        extra_kwargs = {
            'video_link_edited': {'read_only': True},
            'ghost_link_edited': {'read_only': True},
            'comment_edited': {'read_only': True},
            'submitted_by': {'read_only': True},
            'submitted_at': {'read_only': True},
            'reviewed_by': {'read_only': True},
            'reviewed_at': {'read_only': True},
            'reviewer_note': {'read_only': True},
        }


# Standards

class StandardSerializer(serializers.ModelSerializer):
    category = CategoryField()

    class Meta:
        model = models.Standard
        fields = ['id', 'level', 'track', 'category', 'is_lap', 'value']


class StandardLevelSerializer(serializers.ModelSerializer):
    standards = serializers.SerializerMethodField()

    @extend_schema_field(StandardSerializer(many=True))
    def get_standards(self, level: models.StandardLevel):
        return StandardSerializer(
            level.standards.order_by('category', 'track', 'is_lap'),
            many=True,
            context=self.context
        ).data

    class Meta:
        model = models.StandardLevel
        fields = ['id', 'name', 'value', 'is_legacy', 'standards']


# Site Champion

class SiteChampionSerializer(serializers.ModelSerializer):
    category = CategoryField()
    date_instated = TimestampField()
    player = PlayerSerializer()

    class Meta:
        model = models.SiteChampion
        fields = ['id', 'category', 'date_instated', 'player']
