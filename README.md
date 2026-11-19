# Fishkill Little League website

The public pages are static HTML with shared CSS and JavaScript in `assets/`. GitHub Pages serves the committed HTML directly. Updating season data requires Python 3 and uses only its standard library.

## Preview locally

From the repository root, run `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000/). The site uses relative navigation and asset paths so it can also run from the GitHub Pages project URL before the custom domain is connected.

## Publish on GitHub Pages

1. In the repository’s **Settings → Pages**, choose **Deploy from a branch**, then **main** and **/ (root)**. GitHub Free supports Pages for public repositories.
2. After the deployment succeeds, open [the GitHub Pages project URL](https://awalshjamin.github.io/FishkillLittleLeagueWebsite/) and verify the public pages, mobile navigation, and all Sports Connect registration links.
3. When ready to move the live domain, verify ownership in GitHub and add `playfishkill.org` in the repository’s Pages settings. For branch-based publishing, GitHub writes the `CNAME` file. Update the domain’s web DNS records using GitHub’s current instructions and preserve the records used for league email.
4. Enable **Enforce HTTPS** when available. Verify the root domain, `/robots.txt`, `/sitemap.xml` and links to each division. Canonicals and social metadata already use `https://playfishkill.org/`.

[GitHub Pages publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [GitHub Pages custom-domain instructions](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

## Seasonal updates

1. Edit `data/season.json` to update dates, league-age cutoffs, schedules, fees and Sports Connect division IDs. Use ISO dates (`YYYY-MM-DD`).
2. From the repository root, run `python scripts/update-season.py` (or `py -3 scripts/update-season.py` on Windows).
3. Preview the affected pages, check the Sports Connect links, and commit both the JSON and generated HTML. Run `python scripts/update-season.py --check` to check whether the HTML matches the data.

The generator replaces the content between matching `season` comments. Edit family guidance outside those comments directly in `first-season/index.html`. Update the year, roles and names on the About page when a new board takes office. Use the approved sponsor roster and original sponsor artwork for the Sponsors page.

## Replace a page’s hero image

Add the new photo under `assets/images/`. In the page’s `index.html`, update the `src`, `width` and `height` on the `hero-image` element. Keep `./assets/` on the homepage and `../assets/` on pages in subfolders. The hero is decorative behind the page heading, so leave its alternative text empty.

If the same photo is used for social previews, update the Open Graph image URL, dimensions and description, the Twitter image URL and description, and `primaryImageOfPage` in the page’s structured data. Preview the page on a narrow phone and a desktop to check the crop.

## Update the main navigation

Edit `HEADER_LINKS` in `scripts/update-season.py`, then run `python3 scripts/update-season.py` to regenerate the header on every page. Commit the script and updated HTML together. Use `python3 scripts/update-season.py --check` to detect any pages with stale navigation.
