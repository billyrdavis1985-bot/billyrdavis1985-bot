# Interactive project explorer

A static portfolio for the public Hudson Forge repository collection: a searchable and filterable directory, six featured case studies, current research directions, and links to code, demos, and evidence.

## First publication

This repository's GitHub Pages setting must be enabled once by a repository administrator:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Merge the portfolio PR. If it has already merged, open **Actions → Project explorer → Run workflow**, choosing `main`.
4. Open the URL shown by the successful `github-pages` deployment.

The intended default project-site URL is `https://billyrdavis1985-bot.github.io/billyrdavis1985-bot/`. It becomes available after the first successful deployment. The repository file list remains part of GitHub's Code tab; the portfolio is a separate website.

The workflow builds and packages the site even if Pages is not enabled. In that case its summary explicitly says that publication is pending, and the deploy steps are skipped. It does not try to enable Pages using extra credentials.

## Source and data

- `portfolio/projects.json`: the six curated case studies, including their evidence links and scope.
- `portfolio/catalog-overrides.json`: concise descriptions and field assignments for known original repositories.
- `portfolio/repositories.json`: the committed public snapshot used by offline builds and PR validation.
- `portfolio/templates/`, `portfolio/styles.css`, `portfolio/app.js`: static pages and browser interactions.
- `data/research-focus.json`: the same reviewed research directions used by the GitHub profile.
- `scripts/build_portfolio.py`: the standard-library-only builder.

`--refresh` paginates GitHub's public user-repository endpoint and fetches the latest default-branch commit for each public focus project. Private repositories and records owned by other accounts are excluded before rendering or publishing the snapshot. Featured projects that no longer appear in the public inventory are omitted from the generated case studies. Unclassified new original repositories appear under “More research” until a category is reviewed.

Original means GitHub does not mark the repository as a fork. The star total sums original repositories only. The snapshot date is visible; it reports when metadata was fetched, rather than real-time activity. The deployment workflow refreshes daily and on matching source changes. No authenticated browser request or provider API key is needed by a visitor.

## Build and inspect

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
node --check portfolio/app.js
python3 scripts/build_portfolio.py
```

The default build makes no network requests and writes only to its generated output directory, `dist/`. An existing nonempty directory without the builder's marker is refused. To fetch a new public snapshot before building:

```bash
python3 scripts/build_portfolio.py --refresh
```

`GH_TOKEN` is optional for public metadata and helps avoid anonymous API rate limits. It is used only while building; it never appears in the published files. Build output is ignored by Git. The deployment uploads the generated artifact directly; it does not write to `main` or the profile's generated-output branch.

Search, field and language filters, originals/forks selection, sorting, and progressive loading run locally in the browser. Filter state is shareable in the URL. Without JavaScript, the public repository directory and case studies remain readable; interactive controls are disabled. The layout supports narrow screens, keyboard focus, and reduced motion.

Concept illustrations are presentation assets, not photographs of deployed systems. Each case study links to the implementation or evidence and states the limits on its findings.
