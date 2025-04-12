from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from timetrials.models.scores import EditScoreSubmission, ScoreSubmission, ScoreSubmissionStatus
from timetrials.models.stats import PlayerStatsGroup
from timetrials.tasks import generate_player_stats


@receiver(pre_save, sender=ScoreSubmission)
def score_submission_pre_save(sender, instance: ScoreSubmission, **kwargs):
    if instance.status == ScoreSubmissionStatus.ACCEPTED:
        instance.create_score()


@receiver(pre_save, sender=EditScoreSubmission)
def edit_score_submission_pre_save(sender, instance: EditScoreSubmission, **kwargs):
    if instance.status == ScoreSubmissionStatus.ACCEPTED:
        instance.edit_score()


@receiver(post_save, sender=PlayerStatsGroup)
def player_stats_group_post_save(sender, instance: PlayerStatsGroup, created, **kwargs):
    if created:
        generate_player_stats.delay_on_commit(instance.pk)
