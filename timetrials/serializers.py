from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers

from timetrials import models
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
    class Meta:
        model = models.Region
        fields = ['id', 'type', 'name', 'code', 'parent', 'is_ranked']


class RegionStatsSerializer(serializers.ModelSerializer):
    region = RegionSerializer()
    top_score_count = TopScoreCountField()
    category = CategoryField()
    rank = serializers.IntegerField()

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
            'total_standard',
            'total_record_ratio',
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
        fields = ['id', 'name', 'tracks']


# Players

class PlayerBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Player
        fields = ['id', 'name', 'region', 'user', 'alias', 'joined_date', 'last_activity']


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Player
        fields = PlayerBasicSerializer.Meta.fields + ['bio']


class PlayerStatsSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField()
    player = PlayerBasicSerializer()
    category = CategoryField()

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
            'total_standard',
            'total_record_ratio',
            'total_records',
            'leaderboard_points',
        ]


class PlayerMatchupScoreSerializer(serializers.ModelSerializer):
    difference = serializers.IntegerField(allow_null=True)
    category = CategoryField()

    class Meta:
        model = models.Score
        fields = [
            'id',
            'value',
            'difference',
            'player',
            'track',
            'category',
            'is_lap',
            'date',
            'video_link',
            'ghost_link',
            'comment',
        ]


class PlayerMatchupStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlayerStats
        fields = [
            'score_count',
            'total_score',
            'total_rank',
            'total_standard',
            'total_record_ratio',
            'total_records',
            'leaderboard_points',
        ]


class PlayerMatchupPlayerSerializer(serializers.ModelSerializer):
    scores = PlayerMatchupScoreSerializer(many=True, source='player_scores')
    stats = PlayerMatchupStatsSerializer(source='player_stats')
    total_wins = serializers.IntegerField()
    total_ties = serializers.IntegerField()

    class Meta:
        model = models.Player
        fields = ['id', 'name', 'region', 'alias', 'scores', 'stats', 'total_wins', 'total_ties']


class PlayerMatchupSerializer(serializers.Serializer):
    p1 = PlayerMatchupPlayerSerializer()
    p2 = PlayerMatchupPlayerSerializer()


class PlayerAwardSerializer(serializers.ModelSerializer):
    player = PlayerBasicSerializer()

    class Meta:
        model = models.PlayerAward
        fields = ['id', 'player', 'type', 'date', 'description']


# Scores

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
    category = CategoryField()
    status = ScoreSubmissionStatusField(read_only=True)

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
            'status',
            'time_submitted',
            'time_reviewed',
            'reviewed_by',
        ]
        extra_kwargs = {
            'time_submitted': {'read_only': True},
            'time_reviewed': {'read_only': True},
            'reviewed_by': {'read_only': True},
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
