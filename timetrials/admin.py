from django.contrib import admin
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from timetrials import imports, models


# Filters

class RecursiveRegionFilter(admin.SimpleListFilter):
    title = _("region")
    parameter_name = 'region'

    def lookups(self, request, model_admin):
        return [
            (region.id, region.name) for region in models.Region.objects.order_by('parent', 'name')
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        region = models.Region.objects.filter(id=self.value()).first()
        if not region:
            return queryset.none()

        return queryset.filter(region__in=region.descendants(include_self=True).values('pk'))


# Model admins

@admin.register(models.PlayerStatsGroup)
class PlayerStatsGroupAdmin(admin.ModelAdmin):
    fields = ('created_at', 'completed')
    readonly_fields = ('created_at', 'completed')
    list_display = ('id', 'created_at', 'completed')

    def get_deleted_objects(self, objs, request):
        return objs, dict(), set(), list()


class PlayerStatsInline(admin.TabularInline):
    model = models.PlayerStats
    classes = ['collapse']

    def get_queryset(self, request):
        group = models.PlayerStatsGroup.objects.filter(
            completed=True
        ).order_by('-created_at').first()
        return super().get_queryset(request).filter(group=group)

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(models.Player)
class PlayerAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('name', 'region')}),
        ("Other info", {'fields': ('alias', 'bio')}),
        ("Important dates", {'fields': ('joined_date', 'last_activity')}),
    )
    inlines = (PlayerStatsInline,)
    list_display = ('id', 'name', 'alias', 'region', 'user')
    list_display_links = ('name',)
    list_filter = (RecursiveRegionFilter,)
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


@admin.register(models.PlayerSubmitter)
class PlayerSubmitterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('player', 'submitter')}),
    )
    list_display = ('player', 'submitter')
    list_display_links = ('player', 'submitter')
    search_fields = ('player__name', 'submitter__username')
    ordering = ('player__name', 'submitter__username')


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
        ("Details", {'fields': ('date', 'video_link', 'ghost_link', 'comment')}),
        ("Other", {'fields': ('initial_rank', 'submission')}),
        ("Admin", {'fields': ('admin_note',)}),
    )
    readonly_fields = ('initial_rank', 'submission')
    list_display = ('id', 'track', 'category', 'is_lap', '__str__', 'player')
    list_display_links = ('__str__',)
    list_filter = ('track', 'category', 'is_lap')
    search_fields = ('player__name',)
    ordering = ('track', 'category', 'is_lap', 'value')


class SubmissionAdmin(admin.ModelAdmin):
    submission_add_fieldset = (None, {'fields': ('submitter_note',)})
    submission_change_fieldset = (None, {'fields': (
        'status', 'submitted_by', 'submitted_at', 'submitter_note', 'reviewed_by', 'reviewed_at',
        'reviewer_note'
    )})
    submission_readonly_fields = ('submitted_by', 'submitted_at', 'reviewed_by', 'reviewed_at')
    submission_add_readonly_fields = ('status', 'reviewer_note')
    submission_change_readonly_fields = ('submitter_note',)
    ordering = ('submitted_at',)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (self.submission_add_fieldset, *self.fieldsets)
        return (self.submission_change_fieldset, *self.fieldsets)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return (
                self.readonly_fields +
                self.submission_readonly_fields +
                self.submission_add_readonly_fields
            )
        elif obj.is_finalized:
            return flatten_fieldsets(self.get_fieldsets(request, obj))
        return (
            self.readonly_fields +
            self.submission_readonly_fields +
            self.submission_change_readonly_fields
        )

    def save_model(self, request, obj, form, change, **kwargs):
        if change:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        else:
            obj.submitted_by = request.user

        super().save_model(request, obj, form, change, **kwargs)

    def change_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id is not None:
            instance = self.model.objects.filter(id=object_id).first()
            if instance is not None and instance.is_finalized:
                extra_context['show_save'] = False
                extra_context['show_save_and_continue'] = False
                extra_context['show_save_and_add_another'] = False
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(models.ScoreSubmission)
class ScoreSubmissionAdmin(SubmissionAdmin):
    fieldsets = (
        ("Score", {'fields': ('player', 'track', 'value', 'category', 'is_lap')}),
        ("Score details", {'fields': ('date', 'video_link', 'ghost_link', 'comment')}),
        ("Other", {'fields': ('score',)}),
        ("Admin", {'fields': ('admin_note',)}),
    )
    readonly_fields = ('score',)
    list_display = ('id', '__str__', 'submitted_by', 'submitted_at', 'status')
    list_display_links = ('__str__',)
    list_filter = ('status', 'track', 'category', 'is_lap')
    search_fields = ('player__name', 'player__alias')


@admin.register(models.EditScoreSubmission)
class EditScoreSubmissionAdmin(SubmissionAdmin):
    fieldsets = (
        ("Edits", {'fields': (
            'score',
            'video_link_edited', 'video_link',
            'ghost_link_edited', 'ghost_link',
            'comment_edited', 'comment',
        )}),
    )
    raw_id_fields = ('score',)
    list_display = ('id', '__str__', 'submitted_by', 'submitted_at', 'status')
    list_display_links = ('__str__',)
    list_filter = ('status',)
    search_fields = ('score__player__name', 'score__player__alias')
    ordering = ('submitted_at',)


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
        (None, {'fields': ('name', 'code', 'value', 'is_legacy')}),
    )
    list_display = ('id', 'name', 'code', 'value', 'is_legacy')
    list_display_links = ('name',)
    list_filter = ('is_legacy',)
    search_fields = ('name', 'code')
    ordering = ('is_legacy', 'value')


# Custom views

@admin.site.register_view(route='timeimport/', title="Time Importer")
def timeimport(request, context, *args, **kwargs):
    if request.method == 'POST':
        if 'data' not in request.POST or len(request.POST['data']) == 0:
            messages.add_message(request, messages.WARNING,
                                 "Please paste the parser output into the text box below.")

        else:
            try:
                imports.import_from_old_parser(request.POST['data'])
                messages.add_message(request, messages.SUCCESS, "Imported times successfully.")

            except ValueError as e:
                messages.add_message(request, messages.ERROR,
                                     f"An error occured during import. {e}")

    return render(request, 'timetrials/admin/timeupdates.html', context)
