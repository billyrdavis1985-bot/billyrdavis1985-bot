# Public profile visuals

The README displays generated SVG images. GitHub's built-in contribution calendar is controlled by GitHub; the skyline is an additional visualization in the README.

## Contribution skyline

The generator fetches the publicly visible calendar at `https://github.com/users/billyrdavis1985-bot/contributions` without signing in or sending an API token. It reads the date, contribution count, and activity level for each day. The past 365 dates, including the current UTC date, are included. GitHub's current day can still change after the daily refresh.

Each building represents a day. Weeks advance from left to right along the long side of the plane; Sunday through Saturday extend toward its front edge. Month labels follow that front edge. Building height uses `log(1 + contribution count)` to keep very busy days from hiding the rest of the year. Roof color uses GitHub's five activity levels, from dark navy to bright copper. The published JSON preserves the exact daily counts and dates.

The moving light is decorative. It never changes a building's height or contribution count. The animation repeats every 12 seconds. The SVG respects `prefers-reduced-motion`, and the README also selects a separate static SVG for that preference. A static-view link is always available.

Calendar totals are GitHub's publicly displayed profile activity, not a count of commits or a measure of project quality. If the owner chooses to show anonymized private contributions on their public profile, GitHub can include those aggregate counts. No private repository names, commit messages, or source files are collected by this generator. Dates and totals can differ slightly from the native calendar because this view uses an exact 365-day UTC window.

GitHub's public calendar HTML is not a versioned data API. The parser validates every date and count. If GitHub changes the markup or returns an incomplete calendar, generation fails and the existing published files remain in place. The refresh date stays visible on the image.

## Repository statistics

The generator paginates GitHub's public user-repositories API. Every public repository owned by the account is counted, including forks and archived repositories. Private repositories are excluded. The gallery and recent-update feed remain a curated selection of six projects; their size is separate from the account inventory.

“Original” means GitHub does not mark the repository as a fork. Forks have their own directory. The star total sums only original repositories. The language chart counts each original repository once, using GitHub's primary language. It does not claim to measure language proficiency, lines of code, or source-code byte percentages. “Unspecified” means GitHub has not detected a primary language.

## Refresh and reproduce

The existing `Project updates` workflow generates the visuals daily, on manual dispatch, and when matching workflow, generator, focus, or profile-content changes merge into `main`. It publishes the complete output to `profile-updates` only after both generators succeed. Pull-request runs validate and generate previews with read access.

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/update_project_feed.py /tmp/profile-visuals
python3 scripts/render_contributions.py /tmp/profile-visuals
```

Both generators use only Python's standard library. `GH_TOKEN` is optional for public repository metadata and helps avoid anonymous API rate limits. The HTML-calendar request never uses it. SVG files contain no scripts, external fonts, or external images.

## Navigation and research focus

The four category illustrations are static SVG assets, reproduced with `python3 scripts/render_category_cards.py`. Their category pages are curated starting points, with a link to the complete public inventory. The README selects compact category illustrations and a narrower research card for screens up to 640 pixels wide.

The research-focus card combines two kinds of information. Names, stages, next steps, supporting evidence, and their review date are maintained in `data/research-focus.json`. The latest default-branch commit details are fetched daily from GitHub, independently of the release preference in the existing project-update feed. The card displays both the direction-review date and the activity-refresh date. A repository update is not treated as a completed research milestone.

Focus projects must appear in the public original-repository inventory before their activity is fetched. If a focus project becomes private, generation stops before publishing a replacement snapshot. Updating a research direction requires an edit and review of the JSON and its companion page, `docs/current-research.md`.

Sources: [GitHub profile content](https://docs.github.com/en/account-and-profile/concepts/personal-profile), [contribution graph](https://docs.github.com/en/account-and-profile/concepts/contributions-on-your-profile), and [public repository API](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user).
