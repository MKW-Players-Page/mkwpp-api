from celery import shared_task

from timetrials.models.stats import player_stats


@shared_task
def generate_player_stats(group_id=None):
    if group_id is None:
        group = None
    else:
        group = player_stats.PlayerStatsGroup.objects.get(pk=group_id)
    player_stats.generate_all_player_stats(group=group)
