"""Render season content and shared navigation into plain HTML for GitHub Pages."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


HEADER_LINKS = (
    ('baseball', 'Baseball'),
    ('softball', 'Softball'),
    ('winter-clinics', 'Winter Clinics'),
    ('register', 'Register'),
    ('fields', 'Fields'),
    ('volunteer', 'Volunteer'),
    ('sponsors', 'Sponsors'),
    ('donations', 'Donations'),
    ('history', 'History'),
    ('about', 'About'),
)


def site_header(page):
    section = '' if page.parent == ROOT else page.parent.name
    root = './' if not section else '../'
    current = ' aria-current="page"' if not section else ''
    links = []
    for slug, label in HEADER_LINKS:
        active = ' aria-current="page"' if slug == section else ''
        links.append(f'            <a href="{root}{slug}/"{active}>{label}</a>')
    navigation = '\n'.join(links)
    return f"""<header class="site-header">
    <div class="header-inner container">
        <a class="logo-container" href="{root}" aria-label="Fishkill Little League home"{current}>
            <img src="{root}assets/logos/fishkill-logo.png" alt="" width="1563" height="1563">
            <span>Fishkill Little League</span>
        </a>
        <button id="mobile-menu-button" type="button" aria-controls="nav-menu" aria-expanded="false" hidden>Menu</button>
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


def gift_levels(donations):
    return '\n'.join(
        f'            <div><h3>${tier["amount"]:,}</h3><p>{escape(tier["description"])}</p></div>'
        for tier in donations['tiers']
    )



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
        'register-summary': f'''        <h2>{label} at a Glance</h2>
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
        deadline = settings['deadline']
        if deadline is not None:
            try:
                if date.fromisoformat(deadline).isoformat() != deadline:
                    raise ValueError
            except (ValueError, TypeError):
                parser.error(f'Registration setting {group}.deadline must be YYYY-MM-DD or null.')
    donations = json.loads((ROOT / 'data/donations.json').read_text(encoding='utf-8'))
    blocks = regions(season)
    blocks['donation-tiers'] = gift_levels(donations)
    supporter_items = '\n'.join(f'            <li>{escape(name)}</li>' for name in donations['supporters'])
    blocks['donation-supporters'] = f'        <ul>\n{supporter_items}\n        </ul>'
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
