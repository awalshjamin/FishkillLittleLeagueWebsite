"""Render season content and shared navigation into plain HTML for GitHub Pages."""
import argparse
from datetime import date
from html import escape, unescape
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
            f'If your player needs an alternate evaluation, <a data-league-link="email" href="mailto:?subject=Alternate%20player%20evaluation">email the league</a>.</p>'
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


def sponsor_cards(sponsors):
    items = []
    for sponsor in sponsors:
        logo = escape(sponsor['logo'], quote=True)
        content = (
            f'<img src="../{logo}" alt="" width="{int(sponsor["width"])}" height="{int(sponsor["height"])}" '
            f'loading="lazy" decoding="async"><h3>{escape(sponsor["name"])}</h3>'
        )
        if url := sponsor.get('url'):
            content = f'<a href="{escape(url, quote=True)}">{content}</a>'
        items.append(f'            <li class="sponsor-card">{content}</li>')
    return '        <ul class="sponsor-grid">\n' + '\n'.join(items) + '\n        </ul>'


def regions(season):
    label = escape(season['label'])
    opening = time_tag(season['opening_day'], weekday=True)
    rain = time_tag(season['rain_date'])
    evaluations = season['evaluations']
    evaluation_day = time_tag(evaluations['date'], weekday=True)
    evaluation = f'{evaluation_day}, {escape(evaluations["window"])}, at {escape(evaluations["location"])}.'
    attendance = escape(evaluations['requirement'])
    alternate = 'If you can’t attend, <a data-league-link="email" href="mailto:?subject=Alternate%20player%20evaluation">email the league as soon as possible</a> to arrange an alternate evaluation.'
    payment = f'{escape(season["payment_options"])} <a data-league-link="email" href="mailto:?subject=Registration%20payment%20options">Email the league about payment options</a>.'
    uniform = escape(season['uniform'])
    volunteer = f'The league charges one refundable ${season["volunteer_fee"]} volunteer fee per family. The fee is returned at the end of the season after the family volunteers.'
    refund = f'After {season["refund_hours"]} hours from registration submission, refunds require a medical note stating the player cannot participate this season.'
    baseball = season['programs']['baseball']['divisions']
    tee_ball = [item for item in baseball if item.get('practice_day')]
    fundamentals = next(item for item in baseball if item.get('rookie') and not item.get('practice_day'))
    practice_days = list(dict.fromkeys(item['practice_day'] for item in tee_ball))
    tee_overview = f'{season["tee_ball_intro"]} Choose from these practice days when you register: {", ".join(practice_days)}.'
    for item in tee_ball:
        item['name'] = f'Tee Ball {item["practice_day"]}'
        item['description'] = (
            f'{season["tee_ball_intro"]} Practice is on {item["practice_day"]}, with games on '
            f'{item["game_day"]} at {item["game_time"]}.'
        )
        if 'overview' in item:
            item['overview']['description'] = tee_overview
    tee_min = min(item['ages'][0] for item in tee_ball)
    tee_max = max(item['ages'][1] for item in tee_ball)
    tee_ages = f'{tee_min}–{tee_max}' if tee_min != tee_max else str(tee_min)
    fun_age = fundamentals['ages'][0]
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
        'home-rookies-summary': f'                <p>Coed FUN-damentals for age {fun_age} and Tee Ball for ages {tee_ages}. A first step toward baseball or softball.</p>',
        'rookies-fundamentals-age': f'                    <p class="division-meta">Age {fun_age}</p>',
        'rookies-tee-ball-summary': f'                    <p class="division-meta">Ages {tee_ages}</p>\n                    <p>{escape(tee_overview)}</p>',
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


def league_blocks(league):
    eligibility = league['eligibility']
    open_enrollment = escape(eligibility['open_enrollment'])
    older = escape(eligibility['older_players'])
    regulation = escape(eligibility['regulation_url'], quote=True)
    district = escape(eligibility['school_district'])
    schools = ', '.join(escape(school) for school in eligibility['schools'])
    mailing = '<br>'.join(escape(line) for line in league['contact']['mailing_address'])
    eligibility_link = '<a href="../communities/#player-eligibility">check player eligibility</a>'
    return {
        'league-mailing': mailing,
        'registration-eligibility': f'            <p>{open_enrollment} For older players, {eligibility_link} before registering.</p>',
        'about-eligibility': (
            f'        <p>Students at schools in the {district} are eligible. Eligible schools also include {schools}.</p>\n'
            f'        <p>{open_enrollment} {older}. For details, {eligibility_link}.</p>'
        ),
        'community-eligibility': (
            f'        <p>{open_enrollment}</p>\n'
            '        <p>For older players, check your home or school address in the '
            '<a data-league-link="finder" href="">Little League Finder</a>. '
            f'{older} under <a href="{regulation}">Little League’s Regulation II</a>. '
            '<a data-league-link="email" href="mailto:?subject=Player%20eligibility">Email the league</a> '
            'before registering if you need help confirming eligibility.</p>'
        ),
    }


def render_league_links(html, league):
    contact = league['contact']
    destinations = {
        'email': 'mailto:' + contact['email'],
        'phone': 'tel:' + contact['phone_international'].replace('-', ''),
        'finder': league['eligibility']['finder_url'],
        **league['social'],
    }

    # Match the opening tag and any plain visible label, preserving other attributes.
    def replace_anchor(match):
        kind, href, attributes, label = match.groups()
        destination = destinations[kind]
        if kind == 'email' and '?' in href:
            destination += '?' + unescape(href.split('?', 1)[1])
        if kind == 'email' and label == href.removeprefix('mailto:'):
            label = escape(contact['email'])
        elif kind == 'phone':
            label = escape(contact['phone'])
        return f'<a data-league-link="{kind}" href="{escape(destination, quote=True)}"{attributes}>{label}</a>'

    html = re.sub(r'<a data-league-link="([^"]+)" href="([^"]*)"([^>]*)>(.*?)</a>',
                  replace_anchor, html)
    for key, value in {'email': contact['email'], 'telephone': contact['phone_international']}.items():
        html = re.sub(rf'("{key}": )"[^"]*"', lambda m: m[1] + json.dumps(value), html)
    return html


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
    board = json.loads((ROOT / 'data/board.json').read_text(encoding='utf-8'))
    board_rows = '\n'.join(
        f'            <div><dt>{escape(role)}</dt><dd>{escape(name)}</dd></div>'
        for role, name in board['members'].items()
    )
    footer_template = (ROOT / 'scripts/site-footer.html').read_text(encoding='utf-8').rstrip()
    league = json.loads((ROOT / 'data/league.json').read_text(encoding='utf-8'))
    blocks = regions(season)
    blocks.update(league_blocks(league))
    communities = league['eligibility']['served_communities']
    communities_label = ', '.join(communities[:-1]) + ' and ' + communities[-1] if len(communities) > 1 else ''.join(communities)
    blocks['board'] = f"""        <h2>{board['year']} Board of Directors</h2>
        <dl class="board-grid">
{board_rows}
        </dl>"""

    blocks['sponsors'] = sponsor_cards(json.loads((ROOT / 'data/sponsors.json').read_text(encoding='utf-8')))
    blocks['donation-supporters'] = supporter_recognition(donations)
    pattern = re.compile(r'(<!-- season:([\w-]+) -->)\n.*?\n(<!-- /season:\2 -->)', re.S)
    stale = []
    header_pattern = re.compile(r'<header class="site-header">.*?</header>', re.S)
    footer_pattern = re.compile(r'<footer class="site-footer">.*?</footer>', re.S)
    for path in [ROOT / 'index.html', *sorted(ROOT.glob('*/index.html'))]:
        current = path.read_text(encoding='utf-8')
        updated = pattern.sub(lambda m: f'{m[1]}\n{blocks[m[2]]}\n{m[3]}', current)
        updated, header_count = header_pattern.subn(lambda _: site_header(path), updated)
        if header_count != 1:
            parser.error(f'Expected one site header in {path.relative_to(ROOT)}.')
        root = './' if path.parent == ROOT else '../'
        footer = footer_template.replace('@root@', root)
        footer = footer.replace('@communities@', escape(communities_label)).replace('@mailing@', blocks['league-mailing'])
        if path.parent != ROOT:
            href = f'<li><a href="{root}{path.parent.name}/"'
            footer = footer.replace(href, href + ' aria-current="page"')
        updated, footer_count = footer_pattern.subn(lambda _: footer, updated)
        if footer_count != 1:
            parser.error(f'Expected one site footer in {path.relative_to(ROOT)}.')
        updated = render_league_links(updated, league)
        if current != updated:
            if args.check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(updated, encoding='utf-8')
    if stale:
        parser.exit(1, 'Regenerate site content in: ' + ', '.join(stale) + '\n')


if __name__ == '__main__':
    main()
