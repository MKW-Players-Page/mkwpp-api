from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_cte import CTEManager

from core.models import User

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.tracks import Track


def value_to_string(value: int):
    return f"{value // 60000}'{(value % 60000) // 1000:02}\"{value % 1000:03}"


def score_to_string(score):
    return (
        f"{score.track.name} "
        f"[{"Lap" if score.is_lap else "Course"}] "
        f"({CategoryChoices(score.category).label}) - "
        f"{value_to_string(score.value)} - "
        f"{score.player}"
    )


class ScoreSubmissionStatus(models.IntegerChoices):
    PENDING = 0, _("Pending")
    ACCEPTED = 1, _("Accepted")
    REJECTED = 2, _("Rejected")
    ON_HOLD = 3, _("On hold")


class AbstractScore(models.Model):
    value = models.PositiveIntegerField(
        help_text=_("Finish time in milliseconds (e.g. 69999 for 1:09.999).")
    )

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT,
    )

    is_lap = models.BooleanField(default=False, help_text=_("Off for 3lap, on for flap."))

    player = models.ForeignKey(Player, related_name='%(class)ss', on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name='%(class)ss', on_delete=models.CASCADE)

    date = models.DateField(_("date set"), default=timezone.now)

    video_link = models.URLField(max_length=255, null=True, blank=True)
    ghost_link = models.URLField(max_length=255, null=True, blank=True)

    comment = models.CharField(max_length=128, null=True, blank=True)

    admin_note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class Score(AbstractScore):
    objects = CTEManager()

    initial_rank = models.IntegerField(null=True, blank=True)

    @property
    def overall_rank(self) -> int:
        """Calculate the overall rank of this score."""
        return Score.objects.filter(
            track=self.track,
            is_lap=self.is_lap,
            category__lte=self.category,
            value__lt=self.value,
        ).order_by('player', 'value').distinct('player').count() + 1

    def __str__(self):
        return value_to_string(self.value)

    class Meta:
        verbose_name = _("score")
        verbose_name_plural = _("scores")


class AbstractSubmission(models.Model):
    status = models.IntegerField(
        choices=ScoreSubmissionStatus.choices,
        default=ScoreSubmissionStatus.PENDING,
    )

    submitted_by = models.ForeignKey(
        User,
        related_name='own_%(class)ss',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    submitted_at = models.DateTimeField(default=timezone.now)

    submitter_note = models.CharField(max_length=255, null=True, blank=True)

    reviewed_by = models.ForeignKey(
        User,
        related_name='reviewed_%(class)ss',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    reviewer_note = models.CharField(max_length=255, null=True, blank=True)

    @property
    def is_finalized(self) -> bool:
        return self.status in (ScoreSubmissionStatus.ACCEPTED, ScoreSubmissionStatus.REJECTED)

    class Meta:
        abstract = True


class ScoreSubmission(AbstractScore, AbstractSubmission):
    score = models.OneToOneField(
        Score,
        related_name='submission',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def create_score(self):
        """Create a score instance with the data of this submission if not already created."""
        if self.score is not None:
            return

        self.score = Score(
            value=self.value,
            category=self.category,
            is_lap=self.is_lap,
            player=self.player,
            track=self.track,
            date=self.date,
            video_link=self.video_link,
            ghost_link=self.ghost_link,
            comment=self.comment,
        )
        self.score.initial_rank = self.score.overall_rank
        self.score.save()

        self.save()

    def __str__(self):
        return score_to_string(self)

    class Meta:
        verbose_name = _("submission")
        verbose_name_plural = _("submissions")


class EditScoreSubmission(AbstractSubmission):
    score = models.ForeignKey(Score, related_name='edit_submissions', on_delete=models.CASCADE)

    video_link_edited = models.BooleanField(default=False)
    video_link = models.URLField(max_length=255, null=True, blank=True)

    ghost_link_edited = models.BooleanField(default=False)
    ghost_link = models.URLField(max_length=255, null=True, blank=True)

    comment_edited = models.BooleanField(default=False)
    comment = models.CharField(max_length=128, null=True, blank=True)

    def edit_score(self):
        if self.video_link_edited:
            self.score.video_link = self.video_link
        if self.ghost_link_edited:
            self.score.ghost_link = self.ghost_link
        if self.comment_edited:
            self.score.comment = self.comment

        if self.video_link_edited or self.ghost_link_edited or self.comment_edited:
            self.score.save()

    def __str__(self):
        return score_to_string(self.score)

    class Meta:
        verbose_name = _("edit submission")
        verbose_name_plural = _("edit submissions")
