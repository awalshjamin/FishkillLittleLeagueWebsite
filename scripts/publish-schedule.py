"""Publish only allowlisted fields from the private team feeds."""
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from zoneinfo import ZoneInfo


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
    from icalendar import Calendar
    import recurring_ical_events

    calendar = Calendar.from_ical(data)
    return recurring_ical_events.of(calendar).between(lower, upper)


def build_schedule(feeds, now):
    lower = now - timedelta(days=30)
    upper = now + timedelta(days=365)
    events = {}
    for number, (team, url) in enumerate(feeds.items(), 1):
        try:
            items = read_team(url, lower, upper)
            print(f'Source {number}: {len(items)} event occurrences in the publication window.')
            for item in items:
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
    from icalendar import Calendar, Event

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


def configured_teams():
    path = Path(__file__).resolve().parents[1] / 'data/gamechanger-teams.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(config, dict) or any(
        not team.strip() or not isinstance(secret, str)
        or not re.fullmatch(r'GC_FEED_[A-Z0-9_]+', secret)
        for team, secret in config.items()
    ):
        sys.exit('gamechanger-teams.json must map team names to GC_FEED_ secret names.')
    return config


def snapshot(team, path):
    url = os.environ.get('GAMECHANGER_FEED')
    if not url:
        sys.exit(f'Missing GitHub secret: {configured_teams()[team]}')
    events = build_schedule({team: url}, datetime.now(timezone.utc))
    path.write_text(json.dumps([
        [key, {**event, 'start': event['start'].isoformat(),
               'end': event['end'].isoformat(), 'teams': sorted(event['teams'])}]
        for key, event in events.items()
    ]), encoding='utf-8')


def publish_snapshots(directory, destination):
    teams = configured_teams()
    events = {}
    for index in range(len(teams)):
        path = directory / f'gamechanger-{index}' / 'events.json'
        for key, event in json.loads(path.read_text(encoding='utf-8')):
            key = tuple(key)
            if key in events:
                events[key]['teams'].update(event['teams'])
                events[key]['cancelled'] |= event['cancelled']
                continue
            for field in ('start', 'end'):
                value = event[field]
                event[field] = datetime.fromisoformat(value) if 'T' in value else date.fromisoformat(value)
            event['teams'] = set(event['teams'])
            events[key] = event
    publish(destination, datetime.now(timezone.utc), events, teams)
    print(f'Published {len(events)} events from {len(teams)} sources.')


def main():
    if sys.argv[1:] == ['--matrix']:
        config = configured_teams()
        print(json.dumps({'include': [
            {'index': index, 'team': team, 'secret': secret}
            for index, (team, secret) in enumerate(config.items())
        ]}))
        return
    if sys.argv[1:2] == ['--snapshot']:
        try:
            snapshot(sys.argv[2], Path(sys.argv[3]))
        except ValueError as error:
            sys.exit(str(error))
        return
    if sys.argv[1:2] == ['--publish-snapshots']:
        publish_snapshots(Path(sys.argv[2]), Path(sys.argv[3]))
        return
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
