from django.contrib import admin

from timetrials import models


class PlayerStatsInline(admin.TabularInline):
    model = models.PlayerStats
    classes = ['collapse']

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(models.Player)
class PlayerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'region', 'user')}),
        ("Other info", {'fields': ('alias', 'bio')}),
        ("Important dates", {'fields': ('joined_date', 'last_activity')}),
    )
    inlines = (PlayerStatsInline,)
    list_display = ('id', 'name', 'alias', 'region', 'user')
    list_display_links = ('name',)
    list_filter = ('region',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(models.PlayerAward)
class PlayerAwardAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('player', 'type', 'date', 'description')}),
    )
    list_display = ('player', 'type', 'date', 'description')
    list_display_links = ('date',)
    list_filter = ('type',)
    search_fields = ('player__name',)
    ordering = ('type', '-date')


class RegionStatsInline(admin.TabularInline):
    model = models.RegionStats
    classes = ['collapse']

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('type', 'name', 'code', 'parent', 'is_ranked')}),
    )
    inlines = (RegionStatsInline,)
    list_display = ('id', 'type', 'name', 'code', 'parent', 'is_ranked')
    list_display_links = ('name',)
    list_filter = ('type', 'is_ranked', 'parent')
    search_fields = ('name', 'code')
    ordering = ('type', 'parent', 'name')


@admin.register(models.Score)
class ScoreAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('player', 'track', 'value', 'category', 'is_lap')}),
        ("Other info", {'fields': ('date', 'video_link', 'ghost_link')}),
        ("Submission", {'fields': ('status', 'time_submitted', 'time_reviewed', 'reviewed_by')}),
    )
    list_display = ('id', 'track', 'category', 'is_lap', '__str__', 'player', 'status')
    list_display_links = ('__str__',)
    list_filter = ('track', 'category', 'is_lap', 'status')
    search_fields = ('player__name',)
    ordering = ('track', 'category', 'is_lap', 'value')


@admin.register(models.Track)
class TrackAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'abbr', 'cup', 'categories')}),
    )
    list_display = ('id', 'name', 'abbr', 'cup')
    list_display_links = ('name',)
    list_filter = ('cup',)
    search_fields = ('name', 'abbr')
    ordering = ('id',)


@admin.register(models.TrackCup)
class TrackCupAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'code')}),
    )
    list_display = ('id', 'name', 'code')
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(models.Standard)
class StandardAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('level', 'track', 'category', 'is_lap', 'value')}),
    )
    list_display = ('id', 'track', 'category', 'is_lap', 'level', 'value')
    list_display_links = ('value',)
    list_filter = ('track', 'category', 'is_lap', 'level')
    search_fields = ('track__name', 'category__name', 'level__name')
    ordering = ('track', 'category', 'is_lap', 'level__value')


@admin.register(models.StandardLevel)
class StandardLevelAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'value', 'is_legacy')}),
    )
    list_display = ('id', 'name', 'value', 'is_legacy')
    list_display_links = ('name',)
    list_filter = ('is_legacy',)
    search_fields = ('name',)
    ordering = ('is_legacy', 'value')
