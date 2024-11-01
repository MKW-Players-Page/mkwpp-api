from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_cte import CTEManager

from core.models import User

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.tracks import Track


class ScoreSubmissionStatus(models.IntegerChoices):
    PENDING = 0, _("Pending")
    ACCEPTED = 1, _("Accepted")
    REJECTED = 2, _("Rejected")


class Score(models.Model):
    objects = CTEManager()

    value = models.PositiveIntegerField(
        help_text=_("Finish time in milliseconds (e.g. 69999 for 1:09.999).")
    )

    category = models.IntegerField(
        choices=CategoryChoices.choices,
        default=CategoryChoices.NON_SHORTCUT,
    )

    is_lap = models.BooleanField(default=False, help_text=_("Off for 3lap, on for flap."))

    player = models.ForeignKey(Player, related_name='scores', on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name='scores', on_delete=models.CASCADE)

    date = models.DateField(_("date set"), default=timezone.now)

    video_link = models.URLField(max_length=255, null=True, blank=True)
    ghost_link = models.URLField(max_length=255, null=True, blank=True)

    comment = models.CharField(max_length=128, null=True, blank=True)

    # Submission fields

    status = models.IntegerField(
        choices=ScoreSubmissionStatus.choices,
        default=ScoreSubmissionStatus.PENDING,
    )

    time_submitted = models.DateTimeField(default=timezone.now)

    time_reviewed = models.DateTimeField(null=True, blank=True)

    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.value // 60000}'{(self.value % 60000) // 1000:02}\"{self.value % 1000:03}"

    class Meta:
        verbose_name = _("score")
        verbose_name_plural = _("scores")
