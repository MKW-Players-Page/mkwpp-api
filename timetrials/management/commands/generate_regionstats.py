from timeit import timeit

from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("Time taken:", timeit(
            'generate_all_region_stats()',
            setup='from timetrials.models.stats.region_stats import generate_all_region_stats',
            number=1,
            globals=globals()
        ))
