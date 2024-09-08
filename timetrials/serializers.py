from rest_framework import serializers

from timetrials import models


# Regions

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Region
        fields = ['id', 'type', 'name', 'code', 'parent']


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
        fields = [*PlayerBasicSerializer.Meta.fields, 'bio']


# Scores

class ScoreSerializer(serializers.ModelSerializer):
    rank = serializers.SerializerMethodField()

    def _request_category(self):
        """Get category from query params if present."""
        if 'request' not in self.context:
            return None

        request = self.context['request']
        if 'category' not in request.query_params:
            return None

        category = request.query_params['category']
        if category not in models.CategoryChoices.values:
            return None

        return category

    def get_rank(self, score: models.Score) -> int:
        """Return category-aware rank if provided by context."""
        category = self._request_category()
        if category:
            return score.rank_for_category(category)

        return score.rank

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
            'date',
            'video_link',
            'ghost_link',
        ]


class ScoreWithPlayerSerializer(ScoreSerializer):
    player = PlayerBasicSerializer()


# Standards

class StandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Standard
        fields = ['id', 'level', 'track', 'category', 'is_lap', 'value']


class StandardLevelSerializer(serializers.ModelSerializer):
    standards = StandardSerializer(many=True)

    class Meta:
        model = models.StandardLevel
        fields = ['id', 'name', 'value', 'is_legacy', 'standards']
