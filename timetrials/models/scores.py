from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import Player
from timetrials.models.tracks import Track


class Score(models.Model):
    value = models.PositiveIntegerField(
        help_text=_("Finish time in milliseconds (e.g. 69999 for 1:09.999).")
    )

    category = models.CharField(choices=CategoryChoices.choices)
    is_lap = models.BooleanField(default=False, help_text=_("Off for 3lap, on for flap."))

    player = models.ForeignKey(Player, related_name='scores', on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name='scores', on_delete=models.CASCADE)

    date = models.DateField(_("date set"), default=timezone.now)

    video_link = models.URLField(max_length=255, null=True, blank=True)
    ghost_link = models.URLField(max_length=255, null=True, blank=True)

    comment = models.CharField(max_length=128, null=True, blank=True)

    @property
    def related_by_track(self):
        """Return a queryset of scores sharing the same track, category and is_lap values."""
        return Score.objects.filter(track=self.track, category=self.category, is_lap=self.is_lap)

    @property
    def rank(self) -> int:
        """Compute the rank of this score by counting scores with value lower than self."""
        return self.related_by_track.filter(value__lt=self.value).count() + 1

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = _("score")
        verbose_name_plural = _("scores")
