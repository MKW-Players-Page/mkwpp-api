import csv
from datetime import datetime

from django.db import transaction

from timetrials.models import CategoryChoices, Player, Region, Score, Track


COUNTRY_MAP = {
    "USA": "United States",
    "UK": "United Kingdom",
    "Scotland": "United Kingdom",
    "England": "United Kingdom",
    "UAE": "United Arab Emirates",
    "Dominican Rep": "Dominican Republic",
    "Bosnia": "Bosnia and Herzegovina",
}


def import_from_old_parser(data: str):
    """Import times using the CSV output of the old site parser."""

    reader = csv.reader(data.splitlines())

    with transaction.atomic():
        for row in reader:
            if not row or len(row) == 0:
                continue

            if row[0] == 'NEWPLAYER':
                if len(row) != 5:
                    continue

                player_name = row[1]
                player = Player.objects.filter(name__iexact=player_name).first()
                if player:
                    continue

                # unknown = row[2]

                country = COUNTRY_MAP.get(row[3], row[3])
                region = Region.objects.filter(name=country).first()
                if not region:
                    raise ValueError(f"Unknown country: {country}")

                # city = row[4]

                Player.objects.create(
                    name=player_name,
                    region=region,
                )

            else:
                if len(row) != 6:
                    continue

                player_name = row[0]
                player = Player.objects.filter(name__iexact=player_name).first()
                if not player:
                    raise ValueError(f"Unknown player: {player_name}")

                track_raw = row[2]
                try:
                    track_id_raw = int(track_raw)
                except ValueError:
                    raise ValueError(f"Invalid track ID: {track_raw}")

                track_id = (track_id_raw >> 1) + 1
                track = Track.objects.filter(id=track_id).first()
                if not track:
                    raise ValueError(f"Unknown track ID: {track_id_raw}")

                is_lap = (track_id_raw & 1) == 1

                category_raw = row[1]
                if category_raw == 'NonSC':
                    category = CategoryChoices.NON_SHORTCUT
                elif category_raw == 'Combined':
                    category = int(next(reversed(track.categories)))
                else:
                    raise ValueError(f"Invalid category: {category_raw}")

                value_raw = row[3]
                try:
                    value_raw_float = float(value_raw)
                except ValueError:
                    raise ValueError(f"Invalid time value: {value_raw}")

                value = int(value_raw_float * 1000)

                date_raw = row[4]
                try:
                    date = datetime.strptime(date_raw, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Invalid date: {date_raw}")

                video_link = row[5]
                if video_link == 'N/A':
                    video_link = None

                score = Score.objects.filter(
                    player=player,
                    track=track,
                    is_lap=is_lap,
                    category=category,
                    value=value,
                ).first()

                if score:
                    dirty = False

                    if score.date > date:
                        score.date = date
                        dirty = True

                    if score.video_link != video_link:
                        score.video_link = video_link
                        dirty = True

                    if dirty:
                        score.save()

                else:
                    Score.objects.create(
                        player=player,
                        track=track,
                        is_lap=is_lap,
                        category=category,
                        value=value,
                        date=date,
                        video_link=video_link,
                    )
