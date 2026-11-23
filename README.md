# Fishkill Little League website

The public pages are static HTML with shared CSS and JavaScript in `assets/`. GitHub Pages serves the committed HTML directly. Updating season data requires Python 3 and uses only its standard library.

## Preview locally

From the repository root, run `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000/). The site uses relative navigation and asset paths so it can also run from the GitHub Pages project URL before the custom domain is connected.

## Publish on GitHub Pages

1. In the repository’s **Settings → Pages**, choose **Deploy from a branch**, then **main** and **/ (root)**. GitHub Free supports Pages for public repositories.
2. After the deployment succeeds, open [the GitHub Pages project URL](https://awalshjamin.github.io/FishkillLittleLeagueWebsite/) and verify the public pages, mobile navigation, and all Sports Connect registration links.
3. When ready to move the live domain, verify ownership in GitHub and add `fishkilllittleleague.org` in the repository’s Pages settings. For branch-based publishing, GitHub writes the `CNAME` file. Update the domain’s web DNS records using GitHub’s current instructions and preserve the records used for league email.
4. Enable **Enforce HTTPS** when available. Verify the root domain, `/robots.txt`, `/sitemap.xml` and links to each division. Canonicals and social metadata already use `https://fishkilllittleleague.org/`.

[GitHub Pages publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [GitHub Pages custom-domain instructions](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

## Seasonal updates

1. Edit `data/season.json` to update dates, league-age cutoffs, schedules, fees and Sports Connect division IDs. Use ISO dates (`YYYY-MM-DD`). Register and the Season Guide share the same generated summary for evaluations, Opening Day, the volunteer fee, and uniforms and equipment.
2. From the repository root, run `python scripts/update-season.py` (or `py -3 scripts/update-season.py` on Windows).
3. Preview the affected pages, check the Sports Connect links, and commit both the JSON and generated HTML. Run `python scripts/update-season.py --check` to check whether the HTML matches the data.

The generator replaces the content between matching `season` comments. Edit family guidance outside those comments directly in `first-season/index.html`. Update the year, roles and names on the About page when a new board takes office. Use the approved sponsor roster and original sponsor artwork for the Sponsors page.

## Replace a page’s hero image

Add the new photo under `assets/images/`. In the page’s `index.html`, update the `src`, `width` and `height` on the `hero-image` element. Keep `./assets/` on the homepage and `../assets/` on pages in subfolders. The hero is decorative behind the page heading, so leave its alternative text empty.

If the same photo is used for social previews, update the Open Graph image URL, dimensions and description, the Twitter image URL and description, and `primaryImageOfPage` in the page’s structured data. Preview the page on a narrow phone and a desktop to check the crop.

## Update the main navigation

Edit `HEADER_ITEMS` in `scripts/update-season.py`, then run `python3 scripts/update-season.py` to regenerate the header on every page. Commit the script and updated HTML together. Use `python3 scripts/update-season.py --check` to detect any pages with stale navigation.

## Registration deadlines and closing registration

Under `registration` in `data/season.json`, edit `spring` for Baseball, Softball and Rookies, and `winter_clinics` for Winter Clinics. Each has its own settings:

- `"open": true` allows signup links. Use `"open": false` to close immediately after deployment and remove that group's signup links from generated HTML.
- `"deadline": null` leaves the deadline unset. Set a date in `YYYY-MM-DD` format to show it on the site. That date is the final day to register, through 11:59 p.m. Eastern. With JavaScript enabled, the site shows the group as closed and removes its signup links starting the next day.
- Spring also supports optional `clinic_signup_target` and `roster_planning_target` dates. Enter them in chronological order before the spring deadline. The homepage highlights the next milestone and the registration page shows the remaining ones. Messages change after each target date in Eastern time while signup stays open. The clinic target is a planning date for families and does not change the separate Winter Clinics closing setting.

Run `python3 scripts/update-season.py` (or `py -3 scripts/update-season.py` on Windows) and commit both the data and generated pages. Set the matching cutoff in Sports Connect as well. Sports Connect controls whether submissions are accepted, including when someone follows a saved link or has JavaScript disabled.

## Donation supporters

Add supporters to the `supporters` array using one object per card. Set `name` to the approved public name, `url` to the official website, and `logo` to a repository-relative image path. Use `initial` in place of `logo` for a letter badge. The URL and icon are optional. Edit `name` in the same object to rename a supporter. Icons scale with the rendered card, from 20 to 32 CSS pixels.

The page displays general supporters alphabetically, with names beyond the first eight in an expandable list. Use the same object format in `featured_supporters` for more prominent recognition. Featured supporters display in the order listed and are omitted from the general list if the same name appears in both arrays. Keep anonymous names and gift amounts out of the public JSON. Regenerate the page after updating either list.

## GameChanger league schedule

The Season Info page and its single calendar subscription use the same hourly
publish job. Edit `data/gamechanger-teams.json` to add, remove or rename teams.
Each value names a GitHub Actions repository secret beginning with `GC_FEED_`.
In Settings → Secrets and variables → Actions, create each named secret and
paste that team's full GameChanger Schedule Sync URL as its value. Keep URLs
out of commits. Create the two listed clinic secrets before deploying this update.

For local previews, the publisher still accepts the `GAMECHANGER_FEEDS`
environment variable containing a JSON mapping of team names to URLs. GitHub
Actions uses the repo configuration and individual secrets.

After merging the patch, set Settings → Pages → Source to **GitHub Actions**.
Open Actions → Publish website and league schedule and run it manually to
check the first refresh. It also runs on main updates and hourly. Verify the
weekly page and subscription at `/season-info/` after deployment.

Start with the two clinic feeds. Check a reschedule and cancellation before
adding every team. The job only knows about changes reflected in the feeds.
If a source fails, the workflow stops before deploying, so the last published
site remains available. A missing team secret fails the run. An empty team configuration publishes the site with the schedule disabled. Matching iCal event IDs are combined; different IDs are
shown separately. Check GameChanger for last-minute notices.
