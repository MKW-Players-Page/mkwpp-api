from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers

from timetrials import models
from timetrials.models.scores import ScoreSubmissionStatus


# Custom fields

def map_enum_field(mapping: dict):
    reverse = {v: k for k, v in mapping.items()}

    @extend_schema_field(serializers.ChoiceField(choices=mapping.values()))
    class MappedEnumField(serializers.Field):

        def to_representation(self, value):
            return mapping.get(value, None)

        def to_internal_value(self, data):
            return reverse.get(data, None)

    return MappedEnumField


ScoreSubmissionStatusField = map_enum_field({
    ScoreSubmissionStatus.PENDING: 'pending',
    ScoreSubmissionStatus.ACCEPTED: 'accepted',
    ScoreSubmissionStatus.REJECTED: 'rejected',
})


# Regions

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Region
        fields = ['id', 'type', 'name', 'code', 'parent', 'is_ranked']


# Tracks

class TrackSerializer(serializers.ModelSerializer):
    categories = serializers.MultipleChoiceField(choices=models.CategoryChoices.choices)

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


class PlayerStats(serializers.ModelSerializer):
    rank = serializers.IntegerField()
    player = PlayerBasicSerializer()

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


# Scores

class ScoreSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField()
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
