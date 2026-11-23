"""Render season content and shared navigation into plain HTML for GitHub Pages."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


HEADER_ITEMS = (
    ('Programs', (('rookies', 'Rookies'), ('baseball', 'Baseball'), ('softball', 'Softball'), ('winter-clinics', 'Winter Clinics'))),
    ('Register', 'register'),
    ('Season', (('season-guide', 'Season Guide'), ('season-info', 'League Schedule'), ('fields', 'Fields & Directions'))),
    ('Get Involved', (('volunteer', 'Volunteer'), ('sponsors', 'Sponsors'), ('donations', 'Donate'))),
    ('About', (('about', 'About the League'), ('history', 'League History'))),
)


def site_header(page):
    section = '' if page.parent == ROOT else page.parent.name
    root = './' if not section else '../'
    current = ' aria-current="page"' if not section else ''

    def link(slug, label):
        active = ' aria-current="page"' if slug == section else ''
        return f'<a href="{root}{slug}/"{active}>{escape(label)}</a>'

    links = []
    for label, item in HEADER_ITEMS:
        if isinstance(item, str):
            links.append(f'            {link(item, label)}')
            continue
        links.extend((
            '            <details class="nav-group" name="main-navigation">',
            f'                <summary>{escape(label)}</summary>',
            '                <div class="nav-group-links">',
            *(f'                    {link(slug, text)}' for slug, text in item),
            '                </div>',
            '            </details>',
        ))
    navigation = '\n'.join(links)
    return f"""<header class="site-header">
    <div class="header-inner container">
        <a class="logo-container" href="{root}" aria-label="Fishkill Little League home"{current}>
            <img src="{root}assets/logos/fishkill-logo.png" alt="" width="1563" height="1563">
            <span class="logo-name">Fishkill <span>Little League</span></span>
        </a>
        <div class="mobile-header-actions">
            {link('register', 'Register')}
            <button id="mobile-menu-button" type="button" aria-controls="nav-menu" aria-expanded="false" hidden>Menu</button>
        </div>
        <nav id="nav-menu" aria-label="Main navigation">
{navigation}
        </nav>
    </div>
</header>"""



def date_text(value, weekday=False):
    day = date.fromisoformat(value)
    prefix = day.strftime('%A, ') if weekday else ''
    return f'{prefix}{day:%B} {day.day}, {day.year}'


def time_tag(value, weekday=False):
    return f'<time datetime="{value}">{date_text(value, weekday)}</time>'


def registration_status(group, settings, name):
    prefix = f'{name} registration'
    deadline = settings['deadline']
    if not settings['open']:
        return f'<p class="section-intro"><strong>{prefix} is closed.</strong></p>'
    if deadline is None:
        return f'<p class="section-intro"><strong>{prefix} is open.</strong></p>'
    return (
        f'<p class="section-intro" data-registration-status="{group}" '
        f'data-registration-deadline="{deadline}" data-closed-label="{prefix} is closed.">'
        f'<strong>{prefix} closes on {time_tag(deadline)} at 11:59 p.m. Eastern.</strong></p>'
    )


def spring_milestones(settings, prefix):
    if not settings['open']:
        return ''
    clinic = settings.get('clinic_signup_target')
    roster = settings.get('roster_planning_target')
    deadline = settings['deadline']
    messages = []
    if clinic:
        messages.append(
            f'<p data-through="{clinic}"><strong>Planning to attend Winter Clinics? Sign up by '
            f'{time_tag(clinic)}.</strong> Spots are limited, and players must be enrolled in the spring season to participate. '
            f'<a href="{prefix}#winter-clinic-registration">See clinic registration</a>.</p>'
        )
    if roster:
        messages.append(
            f'<p data-through="{roster}"><strong>Register by {time_tag(roster)} to help us form teams and order uniforms.</strong></p>'
        )
    if deadline:
        after = roster or clinic
        after_attribute = f' data-after="{after}" hidden' if after else ''
        messages.append(
            f'<p data-through="{deadline}"{after_attribute}>Spring registration remains open in divisions with space. '
            f'If your player needs an alternate evaluation, <a href="mailto:president@fishkilllittleleague.org?subject=Alternate%20player%20evaluation">email the league</a>.</p>'
        )
    if not messages:
        return ''
    mode = ' data-next-milestone' if prefix else ''
    return f'<div class="section-intro" data-registration-milestones{mode}>\n' + '\n'.join(messages) + '\n</div>'


def supporter_list(supporters, style):
    items = []
    for entry in supporters:
        label = escape(entry["name"])
        icon = ''
        if logo := entry.get('logo'):
            icon = f'<img class="supporter-icon" src="../{escape(logo, quote=True)}" alt="" width="20" height="20" loading="lazy">'
        elif initial := entry.get('initial'):
            icon = f'<span class="supporter-icon supporter-initial" aria-hidden="true">{escape(initial)}</span>'
        if icon:
            icon = f'<span class="supporter-icon-slot">{icon}</span>'
        if url := entry.get('url'):
            content = f'{icon}<span>{label}</span>'
            label = f'<a class="supporter-link" href="{escape(url, quote=True)}">{content}</a>'
        elif icon:
            label = f'<span class="supporter-label">{icon}<span>{label}</span></span>'
        items.append(f'            <li>{label}</li>')
    return f'        <ul class="{style}" role="list">\n' + '\n'.join(items) + '\n        </ul>'


def supporter_entries(entries, details):
    return [
        {**details.get(entry, {}), 'name': entry} if isinstance(entry, str) else entry
        for entry in entries
    ]


def supporter_recognition(donations):
    details = donations.get('supporter_details', {})
    featured = supporter_entries(donations.get('featured_supporters', []), details)
    featured_names = {entry['name'] for entry in featured}
    supporters = sorted(
        (entry for entry in supporter_entries(donations['supporters'], details)
         if entry['name'] not in featured_names),
        key=lambda entry: entry['name'].casefold(),
    )
    sections = []
    if featured:
        sections.append('        <h3>Featured supporters</h3>')
        sections.append(supporter_list(featured, 'supporter-list featured-supporters'))
    if supporters:
        sections.append('        <h3>League supporters</h3>')
        sections.append(supporter_list(supporters[:8], 'supporter-list'))
    if len(supporters) > 8:
        sections.extend([
            '        <details class="supporter-directory">',
            '            <summary>See more league supporters</summary>',
            supporter_list(supporters[8:], 'supporter-list'),
            '        </details>',
        ])
    return '\n'.join(sections)


def cards(program, sport, registration, base_url, registration_open=True):
    output = ['        <div class="division-grid">']
    for item in program['divisions']:
        if not registration and item.get('registration_only'):
            continue
        display = item if registration else item.get('overview', item)
        name = escape(display['name'], quote=True)
        key = item['id']
        low, high = item['ages']
        ages = f'Age {low}' if low == high else f'Ages {low}–{high}'
        if registration:
            href = f'{base_url}?divisionId={key}'
            cta = 'Register'
            label = f'Register for {name}' if sport == 'rookies' else f'Register for {sport.title()} {name}'
            anchor = f'division-{key}'
            fee = f' <span aria-hidden="true">·</span> <span>${item["fee"]}</span>'
        else:
            href = f'../register/#division-{key}'
            cta = 'View registration details'
            label = f'View registration details for {name}'
            anchor = f'program-{key}'
            fee = ''
        signup = f'<a class="btn-primary" href="{escape(href, quote=True)}" aria-label="{label}">{cta}</a>'
        if registration:
            signup = (
                f'<a class="btn-primary" href="{escape(href, quote=True)}" aria-label="{label}" '
                'data-registration-link="spring" data-closed-label="Registration closed">Register</a>'
                if registration_open else '<p>Registration closed</p>'
            )
        output.extend([
            f'            <article class="division-card" id="{anchor}">',
            f'                <h3>{name}</h3>',
            f'                <p class="division-meta">{ages}{fee}</p>',
            f'                <p>{escape(display["description"])}</p>',
            f'                {signup}',
            '            </article>',
        ])
    output.append('        </div>')
    return '\n'.join(output)


def division_table(sport, program):
    rows = []
    for division in program['divisions']:
        low, high = division['ages']
        ages = str(low) if low == high else f'{low}–{high}'
        link = f'<a href="#division-{division["id"]}">{escape(division["name"])}</a>'
        rows.append(f'                <tr><th scope="row">{link}</th><td>{ages}</td></tr>')
    return f"""        <table class="division-table">
            <caption>{sport.title()} divisions by league age</caption>
            <thead><tr><th scope="col">Division</th><th scope="col">League age</th></tr></thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
        </table>"""


def clinic_tables(clinics, registration=False):
    tables = []
    for group in clinics['groups']:
        venue = escape(group['location'])
        day = escape(group['day'])
        rows = []
        for session in group['sessions']:
            name = escape(session['name'])
            if registration:
                href = escape(session["signup_url"], quote=True)
                name = f'<a href="{href}" data-registration-link="winter_clinics">{name}</a>'
            rows.append(f'                <tr><th scope="row">{name}</th><td>{escape(session["time"])}</td></tr>')
        tables.append(f"""        <div>
            <table class="division-table">
                <caption>{day} at {venue}</caption>
                <thead><tr><th scope="col">Clinic</th><th scope="col">Time</th></tr></thead>
                <tbody>
{chr(10).join(rows)}
                </tbody>
            </table>
            <p>{escape(group['address'])}</p>
        </div>""")
    return '        <div class="division-table-grid">\n' + '\n'.join(tables) + '\n        </div>'


def regions(season):
    label = escape(season['label'])
    opening = time_tag(season['opening_day'], weekday=True)
    rain = time_tag(season['rain_date'])
    evaluations = season['evaluations']
    evaluation_day = time_tag(evaluations['date'], weekday=True)
    evaluation = f'{evaluation_day}, {escape(evaluations["window"])}, at {escape(evaluations["location"])}.'
    attendance = escape(evaluations['requirement'])
    alternate = 'If you can’t attend, <a href="mailto:president@fishkilllittleleague.org?subject=Alternate%20player%20evaluation">email the league as soon as possible</a> to arrange an alternate evaluation.'
    payment = f'{escape(season["payment_options"])} <a href="mailto:president@fishkilllittleleague.org?subject=Registration%20payment%20options">Email the league about payment options</a>.'
    uniform = escape(season['uniform'])
    volunteer = f'The league charges one refundable ${season["volunteer_fee"]} volunteer fee per family. The fee is returned at the end of the season after the family volunteers.'
    refund = f'After {season["refund_hours"]} hours from registration submission, refunds require a medical note stating the player cannot participate this season.'
    registration_programs = {'rookies': {'divisions': [
        item for item in season['programs']['baseball']['divisions'] if item.get('rookie')
    ]}}
    for sport, program in season['programs'].items():
        registration_programs[sport] = {'divisions': [
            item for item in program['divisions'] if not item.get('rookie')
        ]}
    clinics = season['winter_clinics']
    spring_registration = season['registration']['spring']
    clinic_registration = season['registration']['winter_clinics']
    clinic_cta = (
        f'<p class="section-action" data-registration-link="winter_clinics"><a href="{escape(clinics["sessions_url"], quote=True)}">View all programs in Sports Connect</a></p>'
        if clinic_registration['open'] else ''
    )
    start = time_tag(clinics['starts'])
    end = time_tag(clinics['ends'])
    clinic_summary = f'<p class="section-intro">Clinics run from {start} through {end}. Each clinic costs ${clinics["fee"]}. <strong>Players must be registered for Fishkill Little League’s {label} season to participate.</strong></p>'
    rookies_cutoff = time_tag(season['programs']['baseball']['cutoff'])
    rookies_exception = escape(season['rookies_age_exception'])
    blocks = {
        'spring-registration-status': registration_status('spring', spring_registration, 'Spring'),
        'home-registration-milestones': spring_milestones(spring_registration, './register/'),
        'register-milestones': spring_milestones(spring_registration, ''),
        'clinic-registration-status': registration_status('winter_clinics', clinic_registration, 'Winter clinic'),
        'rookies-age': f'<p class="section-intro">FUN-damentals and Tee Ball are open to boys and girls. Tee Ball uses your child’s age on {rookies_cutoff}. {rookies_exception}</p>',
        'clinic-summary': clinic_summary,
        'clinic-schedule': clinic_tables(clinics),
        'clinic-registration': clinic_tables(clinics, registration=clinic_registration['open']),
        'clinic-listing-link': clinic_cta,
        'rookies-registration': cards(registration_programs['rookies'], 'rookies', True, season['registration_url'], spring_registration['open']),
        'home-label': f'                {label} Registration',
        'home-dates': f'''            <h3>Opening Day</h3>
            <p>{opening}, weather permitting.</p>
            <h3>Rain date</h3>
            <p>{rain}</p>
            <h3>Player evaluations</h3>
            <p>{evaluation}</p>''',
        'register-intro': f'            Compare {label.lower()} divisions and register through Sports Connect.',
        'season-at-a-glance': f'''        <h2>{label} at a Glance</h2>
        <div class="season-details">
            <div><h3>Player evaluations</h3><p>{evaluation} {attendance} {alternate} Players are assigned a slot of {escape(evaluations["slot"])}. Details are expected in {escape(evaluations["details_release"])}.</p></div>
            <div><h3>Opening Day</h3><p>{opening}, weather permitting. Rain date {rain}. Ceremony details are expected in {escape(season["opening_details_release"])}.</p></div>
            <div><h3>Volunteer fee</h3><p>{volunteer} <a href="../volunteer/">Explore volunteer opportunities</a>.</p></div>
            <div><h3>Uniforms &amp; equipment</h3><p>{uniform}</p></div>
        </div>''',
        'register-payment': f'            <div><h3>Payment plans &amp; financial assistance</h3><p>{payment}</p></div>',
        'register-refund': f'            <div><h3>Refund policy</h3><p>{refund}</p></div>',
        'guide-season': f'''                <p>{evaluation} {attendance} {alternate} Expect an assigned slot of {escape(evaluations["slot"])} and more details in {escape(evaluations["details_release"])}.</p>
                <p>Opening Day is {opening}, weather permitting. The rain date is {rain}. Games run through {escape(season["season_end"])}.</p>''',
        'guide-schedule': f'        <p>{escape(season["team_schedule"])} {escape(season["weeknight_games"])} {escape(season["possible_travel"])}</p>',
        'guide-uniform': f'        <p>{uniform}</p>',
        'guide-payment': f'        <p>{payment}</p>',
        'division-tables': '        <div class="division-table-grid">\n' + '\n'.join(
            division_table(sport, program) for sport, program in registration_programs.items()
        ) + '\n        </div>',
        'guide-fee': f'                <p>{volunteer} See <a href="../volunteer/">ways to volunteer</a>, including coaching, serving as a team parent, field maintenance, concessions and fundraising.</p>',
    }
    for sport, program in season['programs'].items():
        guide_intro = f'{sport.title()} league age is based on your child’s age on {time_tag(program["cutoff"])}. {escape(program["placement_note"])}'
        if sport == 'baseball':
            guide_intro += f' {rookies_exception}'
        blocks[f'{sport}-age'] = f'        <p class="section-intro">{guide_intro}</p>'
        blocks[f'guide-{sport}-age'] = f'                <p>{guide_intro}</p>'
        blocks[f'guide-{sport}-practices'] = f'                <p>{escape(program["practices"])}</p>'
        for registration in (False, True):
            suffix = 'registration' if registration else 'programs'
            blocks[f'{sport}-{suffix}'] = cards(registration_programs[sport] if registration else program, sport, registration, season['registration_url'], spring_registration['open'])
    return blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Report stale output without writing')
    args = parser.parse_args()
    season = json.loads((ROOT / 'data/season.json').read_text(encoding='utf-8'))
    ids = [row['id'] for program in season['programs'].values() for row in program['divisions']]
    ids.extend(session['id'] for group in season['winter_clinics']['groups'] for session in group['sessions'])
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[0-9]+', key) for key in ids):
        parser.error('Each division must have a unique numeric Sports Connect ID.')
    for group in ('spring', 'winter_clinics'):
        settings = season['registration'][group]
        if not isinstance(settings['open'], bool):
            parser.error(f'Registration setting {group}.open must be true or false.')
        for key in ('deadline', 'clinic_signup_target', 'roster_planning_target'):
            value = settings.get(key)
            if value is None:
                continue
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except (ValueError, TypeError):
                parser.error(f'Registration setting {group}.{key} must be YYYY-MM-DD or null.')
    spring = season['registration']['spring']
    dates = [spring.get(key) for key in ('clinic_signup_target', 'roster_planning_target', 'deadline')]
    dates = [value for value in dates if value]
    if dates != sorted(set(dates)):
        parser.error('Spring registration milestones must be in order and precede the final deadline.')
    donations = json.loads((ROOT / 'data/donations.json').read_text(encoding='utf-8'))
    blocks = regions(season)
    blocks['donation-supporters'] = supporter_recognition(donations)
    pattern = re.compile(r'(<!-- season:([\w-]+) -->)\n.*?\n(<!-- /season:\2 -->)', re.S)
    stale = []
    header_pattern = re.compile(r'<header class="site-header">.*?</header>', re.S)
    for path in [ROOT / 'index.html', *sorted(ROOT.glob('*/index.html'))]:
        current = path.read_text(encoding='utf-8')
        updated = pattern.sub(lambda m: f'{m[1]}\n{blocks[m[2]]}\n{m[3]}', current)
        updated, header_count = header_pattern.subn(lambda _: site_header(path), updated)
        if header_count != 1:
            parser.error(f'Expected one site header in {path.relative_to(ROOT)}.')
        if current != updated:
            if args.check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(updated, encoding='utf-8')
    if stale:
        parser.exit(1, 'Regenerate site content in: ' + ', '.join(stale) + '\n')


if __name__ == '__main__':
    main()
