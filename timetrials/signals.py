from django.db.models.signals import pre_save
from django.dispatch import receiver

from timetrials.models.scores import ScoreSubmission, ScoreSubmissionStatus


@receiver(pre_save, sender=ScoreSubmission)
def score_submission_post_save(sender, instance: ScoreSubmission, **kwargs):
    if instance.status == ScoreSubmissionStatus.ACCEPTED:
        instance.create_score()
