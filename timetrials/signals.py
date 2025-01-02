from django.db.models.signals import pre_save
from django.dispatch import receiver

from timetrials.models.scores import EditScoreSubmission, ScoreSubmission, ScoreSubmissionStatus


@receiver(pre_save, sender=ScoreSubmission)
def score_submission_pre_save(sender, instance: ScoreSubmission, **kwargs):
    if instance.status == ScoreSubmissionStatus.ACCEPTED:
        instance.create_score()


@receiver(pre_save, sender=EditScoreSubmission)
def edit_score_submission_pre_save(sender, instance: EditScoreSubmission, **kwargs):
    if instance.status == ScoreSubmissionStatus.ACCEPTED:
        instance.edit_score()
