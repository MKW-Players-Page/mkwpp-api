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

    player = models.ForeignKey(Player, related_name='%(class)s', on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name='%(class)s', on_delete=models.CASCADE)

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
        related_name='own_%(class)s',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    submitted_at = models.DateTimeField(default=timezone.now)

    submitter_note = models.CharField(max_length=255, null=True, blank=True)

    reviewed_by = models.ForeignKey(
        User,
        related_name='reviewed_%(class)s',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    reviewer_note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class ScoreSubmission(AbstractScore, AbstractSubmission):

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

    def __str__(self):
        return score_to_string(self.score)

    class Meta:
        verbose_name = _("edit submission")
        verbose_name_plural = _("edit submissions")
