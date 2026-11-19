# Fishkill Little League website

The nine public pages are static HTML with shared CSS and JavaScript in `assets/`. No build, framework, or paid hosting is required to serve this checkout.

## Preview locally

From the repository root, run `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000/). The site uses relative navigation and asset paths so it can also run from the GitHub Pages project URL before the custom domain is connected.

## Publish on GitHub Pages

1. In the repository’s **Settings → Pages**, choose **Deploy from a branch**, then **main** and **/ (root)**. GitHub Free supports Pages for public repositories.
2. After the deployment succeeds, open [the GitHub Pages project URL](https://awalshjamin.github.io/FishkillLittleLeagueWebsite/) and verify the nine pages, mobile navigation, and all Sports Connect registration links.
3. When ready to move the live domain, verify ownership in GitHub and add `fishkilllittleleague.org` in the repository’s Pages settings. For branch-based publishing, GitHub writes the `CNAME` file. Update the domain’s web DNS records using GitHub’s current instructions and preserve the records used for league email.
4. Enable **Enforce HTTPS** when available. Verify the root domain, `/robots.txt`, `/sitemap.xml` and links to each division. Canonicals and social metadata already use `https://fishkilllittleleague.org/`.

[GitHub Pages publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [GitHub Pages custom-domain instructions](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

## Seasonal updates

Update dates and registration callouts on the homepage and registration page, and keep the division cards on the Baseball, Softball and Register pages in sync with the published Sports Connect listings. Update the year, roles and names on the About page when a new board takes office. Use the approved sponsor roster and original sponsor artwork for the Sponsors page.
