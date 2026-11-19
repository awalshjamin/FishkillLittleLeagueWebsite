"""Render editable season data into plain HTML for GitHub Pages."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def date_text(value, weekday=False):
    day = date.fromisoformat(value)
    prefix = day.strftime('%A, ') if weekday else ''
    return f'{prefix}{day:%B} {day.day}, {day.year}'


def time_tag(value, weekday=False):
    return f'<time datetime="{value}">{date_text(value, weekday)}</time>'


def cards(program, sport, registration, base_url):
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
        output.extend([
            f'            <article class="division-card" id="{anchor}">',
            f'                <h3>{name}</h3>',
            f'                <p class="division-meta">{ages}{fee}</p>',
            f'                <p>{escape(display["description"])}</p>',
            f'                <a class="btn-primary" href="{escape(href, quote=True)}" aria-label="{label}">{cta}</a>',
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
                name = f'<a href="{href}">{name}</a>'
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
    start = time_tag(clinics['starts'])
    end = time_tag(clinics['ends'])
    clinic_summary = f'<p class="section-intro">Clinics run from {start} through {end}. Each clinic costs ${clinics["fee"]}. <strong>Players must be registered for Fishkill Little League’s {label} season to participate.</strong></p>'
    rookies_cutoff = time_tag(season['programs']['baseball']['cutoff'])
    rookies_exception = escape(season['rookies_age_exception'])
    blocks = {
        'rookies-age': f'<p class="section-intro">FUN-damentals and Tee Ball are open to boys and girls. Tee Ball uses your child’s age on {rookies_cutoff}. {rookies_exception}</p>',
        'clinic-summary': clinic_summary,
        'clinic-schedule': clinic_tables(clinics),
        'clinic-registration': clinic_tables(clinics, registration=True),
        'clinic-listing-link': f'<p class="section-action"><a href="{escape(clinics["sessions_url"], quote=True)}">View all programs in Sports Connect</a></p>',
        'rookies-registration': cards(registration_programs['rookies'], 'rookies', True, season['registration_url']),
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
            <div><h3>Volunteer fee</h3><p>{volunteer}</p></div>
            <div><h3>Uniforms &amp; equipment</h3><p>{uniform}</p></div>
            <div><h3>Payment plans &amp; financial assistance</h3><p>{payment}</p></div>
            <div><h3>Refund policy</h3><p>{refund}</p></div>
        </div>''',
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
            blocks[f'{sport}-{suffix}'] = cards(registration_programs[sport] if registration else program, sport, registration, season['registration_url'])
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
    blocks = regions(season)
    pattern = re.compile(r'(<!-- season:([\w-]+) -->)\n.*?\n(<!-- /season:\2 -->)', re.S)
    stale = []
    for page in ('index.html', 'baseball/index.html', 'softball/index.html', 'register/index.html', 'first-season/index.html', 'winter-clinics/index.html'):
        path = ROOT / page
        current = path.read_text(encoding='utf-8')
        updated = pattern.sub(lambda m: f'{m[1]}\n{blocks[m[2]]}\n{m[3]}', current)
        if current != updated:
            if args.check:
                stale.append(page)
            else:
                path.write_text(updated, encoding='utf-8')
    if stale:
        parser.exit(1, 'Regenerate season content in: ' + ', '.join(stale) + '\n')


if __name__ == '__main__':
    main()
