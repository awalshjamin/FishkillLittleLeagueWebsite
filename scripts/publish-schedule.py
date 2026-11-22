"""Publish only allowlisted fields from the private team feeds."""
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event
import recurring_ical_events

EASTERN = ZoneInfo('America/New_York')


def normalized_time(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or EASTERN).astimezone(timezone.utc)
    if isinstance(value, date):
        return value
    raise ValueError('Unsupported event date')


def read_team(url, lower, upper):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.netloc != 'api.team-manager.gc.com':
        raise ValueError('Expected a GameChanger HTTPS feed')
    with urlopen(url, timeout=20) as response:
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError('Feed exceeds size limit')
    calendar = Calendar.from_ical(data)
    return recurring_ical_events.of(calendar).between(lower, upper)


def build_schedule(feeds, now):
    lower = now - timedelta(days=30)
    upper = now + timedelta(days=365)
    events = {}
    for number, (team, url) in enumerate(feeds.items(), 1):
        try:
            for item in read_team(url, lower, upper):
                start = normalized_time(item.decoded('DTSTART'))
                end = normalized_time(item.decoded('DTEND')) if 'DTEND' in item else (
                    start + item.decoded('DURATION') if 'DURATION' in item else
                    start + timedelta(days=1) if type(start) is date else start
                )
                uid = str(item['UID'])
                occurrence = item.get('RECURRENCE-ID')
                key = (uid, normalized_time(occurrence.dt).isoformat() if occurrence else '')
                status = str(item.get('STATUS', '')).upper()
                if key in events:
                    events[key]['teams'].add(team)
                    if status == 'CANCELLED':
                        events[key]['cancelled'] = True
                    continue
                events[key] = dict(
                    title=str(item.get('SUMMARY', 'Team event')),
                    location=str(item.get('LOCATION', '')),
                    notes=str(item.get('DESCRIPTION', '')),
                    start=start, end=end, cancelled=status == 'CANCELLED', teams={team},
                )
        except Exception:
            raise ValueError(f'Source {number} could not be read. Existing deployment is preserved.') from None
    return events


def publish(destination, now, events, teams):
    calendar = Calendar()
    calendar.add('prodid', '-//Fishkill Little League//League Schedule//EN')
    calendar.add('version', '2.0')
    calendar.add('x-wr-calname', 'Fishkill Little League Schedule')
    rows = []
    for key, data in sorted(events.items(), key=lambda pair: pair[1]['start'].isoformat()):
        start, end = data['start'], data['end']
        event = Event()
        event.add('uid', hashlib.sha256(json.dumps(key).encode()).hexdigest() + '@fishkilllittleleague.org')
        event.add('dtstamp', now)
        event.add('dtstart', start)
        if end > start:
            event.add('dtend', end)
        if data['cancelled']:
            event.add('status', 'CANCELLED')
        event.add('summary', ('Cancelled: ' if data['cancelled'] else '') + data['title'])
        event.add('location', data['location'])
        calendar.add_component(event)
        rows.append({**data, 'start': start.isoformat(), 'end': end.isoformat(),
                     'teams': sorted(data['teams'])})
    (destination / 'schedule.json').write_text(json.dumps({
        'updated': now.isoformat(), 'configured': bool(teams),
        'teams': sorted(teams), 'events': rows,
    }), encoding='utf-8')
    (destination / 'schedule.ics').write_bytes(calendar.to_ical())


def main():
    try:
        feeds = json.loads(os.environ.get('GAMECHANGER_FEEDS') or '{}')
    except ValueError:
        sys.exit('GAMECHANGER_FEEDS must be a JSON object.')
    if not isinstance(feeds, dict) or any(
        not team.strip() or not isinstance(url, str) for team, url in feeds.items()
    ):
        sys.exit('GAMECHANGER_FEEDS must map team names to feed URLs.')
    now = datetime.now(timezone.utc)
    try:
        events = build_schedule(feeds, now)
    except ValueError as error:
        sys.exit(str(error))
    publish(Path(sys.argv[1]), now, events, feeds)
    print(f'Published {len(events)} events from {len(feeds)} sources.')


if __name__ == '__main__':
    main()
