"""Build the static project explorer, optionally refreshing public GitHub data.

The default build is offline and uses the committed public snapshot. --refresh
reads only public repositories and two public default-branch commit endpoints.
No model calls, third-party packages, or browser-side GitHub requests are used.
"""

import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import shutil
from string import Template
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OWNER = "billyrdavis1985-bot"
SNAPSHOT = ROOT / "portfolio" / "repositories.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def github_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Hudson-Forge-Portfolio",
               "X-GitHub-Api-Version": "2026-03-10"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    with urlopen(Request(f"https://api.github.com/{path}", headers=headers), timeout=20) as response:
        return json.load(response)


def public_repositories(repositories):
    """Reject private or unrelated records even if an input snapshot is edited."""
    result = {}
    for repo in repositories:
        if repo.get("private") is not False or repo.get("owner", "").lower() != OWNER.lower():
            continue
        name = repo["name"]
        if not name or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in name):
            raise ValueError("Invalid public repository name")
        result[name] = repo
    if not result:
        raise ValueError("The public repository snapshot is empty")
    return sorted(result.values(), key=lambda item: item["name"].lower())


def refresh_snapshot():
    records = []
    page = 1
    while True:
        batch = github_json(f"users/{OWNER}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        for repo in batch:
            if repo["private"] or repo.get("visibility", "public") != "public" or repo["owner"]["login"].lower() != OWNER.lower():
                continue
            records.append({"name": repo["name"], "owner": repo["owner"]["login"], "private": False,
                            "description": repo["description"] or "", "language": repo["language"] or "Unspecified",
                            "stars": repo["stargazers_count"], "fork": repo["fork"], "archived": repo["archived"],
                            "updated": repo["pushed_at"] or repo["created_at"]})
        if len(batch) < 100:
            break
        page += 1
    records = public_repositories(records)
    names = {repo["name"] for repo in records if not repo["fork"]}
    focus = read_json(ROOT / "data" / "research-focus.json")
    commits = {}
    for item in focus["items"]:
        if item["repository"] not in names:
            continue
        entry = github_json(f"repos/{OWNER}/{item['repository']}/commits?per_page=1")[0]
        message = [line.strip() for line in entry["commit"]["message"].splitlines() if line.strip()]
        title = message[1] if message[0].startswith("Merge pull request #") and len(message) > 1 else message[0]
        commits[item["repository"]] = {"sha": entry["sha"], "date": entry["commit"]["committer"]["date"], "title": title}
    return {"schema": 1, "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "owner": OWNER, "repositories": records, "research_commits": commits}


def repo_url(name):
    return f"https://github.com/{OWNER}/{quote(name, safe='')}"


def html_link(label, url, css=""):
    if not url.startswith("https://"):
        raise ValueError("External links must use HTTPS")
    return f'<a class="{escape(css, quote=True)}" href="{escape(url, quote=True)}">{escape(label)} <svg class="arrow" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M3 3h10v10"/></svg></a>'


def date_label(value):
    return datetime.fromisoformat(value).strftime("%b %d, %Y")


def render_base(body, title, description, snapshot_date, nested=False, script=None):
    prefix = "../../" if nested else ""
    return Template((ROOT / "portfolio/templates/base.html").read_text()).substitute(
        body=body, title=escape(title, quote=True), description=escape(description, quote=True),
        prefix=prefix, home="../../" if nested else "./", snapshot_date=escape(snapshot_date),
        scripts=f'<script src="{prefix}assets/{script}" defer></script>' if script else "",
    )


def feature_card(project, categories):
    slug, name = project["slug"], project["name"]
    category = escape(categories[project["category"]]["name"])
    replay = project.get("replay")
    if replay:
        highlights = "".join(
            f"<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>"
            for label, value in replay["highlights"].items()
        )
        return (
            f'<article class="feature-card feature-replay"><div class="feature-copy">'
            f'<p class="category-label">{category} · Recorded demo</p>'
            f'<h3><a href="projects/{slug}/">{escape(name)}</a></h3>'
            f'<p>{escape(project["summary"])}</p>'
            f'<a href="projects/{slug}/#replay">{escape(replay["action"])}</a></div>'
            f'<dl class="feature-replay-outcome">{highlights}</dl></article>'
        )
    return (f'<article class="feature-card"><a class="feature-image" href="projects/{slug}/" tabindex="-1" aria-hidden="true">'
            f'<img src="{escape(project["image"], quote=True)}" alt="" width="640" height="415" loading="lazy"></a>'
            f'<div class="feature-copy"><p class="category-label">{category}</p>'
            f'<h3><a href="projects/{slug}/">{escape(name)}</a></h3><p>{escape(project["summary"])}</p>'
            f'<a href="projects/{slug}/" aria-label="Explore {escape(name, quote=True)} case study">Explore the work <svg class="arrow" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M3 3h10v10"/></svg></a></div></article>')


def collection_cards(categories, originals, overrides):
    counts = dict.fromkeys(categories, 0)
    for repo in originals:
        field = overrides.get(repo["name"], {}).get("category")
        if field in counts:
            counts[field] += 1

    cards = []
    for field, category in categories.items():
        count = counts[field]
        if not count:
            continue
        count_label = "project" if count == 1 else "projects"
        cards.append(
            f'<a class="collection-card" href="?field={quote(field, safe="")}#explore">'
            f'<strong>{escape(category["name"])}</strong>'
            f'<span>{escape(category["description"])}</span>'
            f'<small>{count} original {count_label}</small></a>'
        )
    if not cards:
        return ""
    return (
        '<section class="section-wrap collection-section" aria-labelledby="collections-title">'
        '<h2 id="collections-title">Browse by field</h2>'
        '<div class="collection-grid">' + "\n".join(cards) + '</div></section>'
    )


def repository_row(repo, override, categories, featured):
    name = repo["name"]
    title = override.get("title", name)
    category = override.get("category", "tools" if repo["fork"] else "other")
    field = categories.get(category, {"name": "More research"})["name"]
    description = override.get("description", repo["description"] or "Open the repository to explore the source and documentation.")
    if len(description) > 220:
        description = description[:217].rstrip() + "…"
    kind = "fork" if repo["fork"] else "original"
    label = "Fork" if repo["fork"] else "Original"
    search = " ".join((name, title, description, field, repo["language"]))
    attrs = {"name": title, "category": category, "language": repo["language"], "kind": kind,
             "stars": str(repo["stars"]), "updated": repo["updated"], "search": search}
    data_attrs = " ".join(f'data-{key}="{escape(value, quote=True)}"' for key, value in attrs.items())
    study = f'<a href="projects/{featured[name]}/">Case study</a>' if name in featured else ""
    archived = '<span class="repo-type">Archived</span>' if repo["archived"] else ""
    return (f'<article class="repo-item" {data_attrs}><div><h3><a href="{repo_url(name)}">{escape(title)} <svg class="arrow" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 13 13 3M3 3h10v10"/></svg></a></h3>'
            f'<p>{escape(description)}</p><div class="repo-meta"><span class="repo-field">{escape(field)}</span>'
            f'<span>{escape(repo["language"])}</span><span class="repo-type">{label}</span>{archived}{study}</div></div>'
            f'<div class="repo-stats"><span class="star-count">☆ {repo["stars"]} {"star" if repo["stars"] == 1 else "stars"}</span>'
            f'<span>Updated {date_label(repo["updated"])}</span></div></article>')


def research_tracks(focus, snapshot, names, replays):
    tracks = []
    for item in focus["items"]:
        repo = item["repository"]
        if repo not in names:
            continue
        commit = snapshot["research_commits"].get(repo)
        activity = ""
        if commit:
            activity = (f'<a class="commit-link" href="{repo_url(repo)}/commit/{escape(commit["sha"], quote=True)}">'
                        f'<span>Latest commit · {date_label(commit["date"])}</span>{escape(commit["title"])}</a>')
        replay_link = ""
        if repo in replays:
            project = replays[repo]
            replay_link = (f'<a class="direction-link" href="projects/{project["slug"]}/#replay">'
                           f'{escape(project["replay"]["action"])}</a>')
        tracks.append(f'<article class="research-track"><div class="track-top"><h3><a href="{repo_url(repo)}">{escape(item["name"])}</a></h3>'
                      f'<span class="stage">{escape(item["stage"])}</span></div><p class="track-next">Next: {escape(item["next"])}</p>'
                      f'{activity}{html_link("Evidence for the direction", item["evidence"], "direction-link")}{replay_link}</article>')
    return "\n".join(tracks)


def build_site(snapshot, output):
    if snapshot.get("schema") != 1 or snapshot.get("owner") != OWNER:
        raise ValueError("Unrecognized public repository snapshot")
    repositories = public_repositories(snapshot["repositories"])
    names = {repo["name"] for repo in repositories if not repo["fork"]}
    projects = [p for p in read_json(ROOT / "portfolio/projects.json") if p["repository"] in names]
    categories = read_json(ROOT / "portfolio/categories.json")
    overrides = read_json(ROOT / "portfolio/catalog-overrides.json")
    focus = read_json(ROOT / "data/research-focus.json")
    date = snapshot["captured_at"][:10]
    originals = [repo for repo in repositories if not repo["fork"]]
    featured = {project["repository"]: project["slug"] for project in projects}
    replays = {project["repository"]: project for project in projects if project.get("replay")}
    if output.exists() and any(output.iterdir()) and not (output / ".portfolio-build").is_file():
        raise ValueError("Refusing to overwrite a directory not owned by this builder")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".portfolio-build-", dir=output.parent) as temporary:
        stage = Path(temporary) / "site"
        (stage / "assets/projects").mkdir(parents=True)
        (stage / ".portfolio-build").write_text("Generated by scripts/build_portfolio.py\n")
        (stage / ".nojekyll").write_text("")
        for filename in ("styles.css", "app.js", "replay.js"):
            shutil.copyfile(ROOT / "portfolio" / filename, stage / "assets" / filename)
        for path in (ROOT / "portfolio/static").iterdir():
            if path.is_file():
                shutil.copyfile(path, stage / "assets" / path.name)
        shutil.copyfile(ROOT / "assets/hudson-forge-banner.webp", stage / "assets/hudson-forge-banner.webp")
        for project in projects:
            if "image" not in project:
                continue
            image = Path(project["image"])
            if image.parts[:2] == ("assets", "projects"):
                shutil.copyfile(ROOT / image, stage / image)
        safe_snapshot = dict(snapshot, repositories=repositories,
                             research_commits={key: value for key, value in snapshot["research_commits"].items() if key in names})
        (stage / "assets/repositories.json").write_text(json.dumps(safe_snapshot, indent=2) + "\n", encoding="utf-8")
        values = [(len(repositories), "public repositories"), (len(originals), "original projects"),
                  (len(repositories) - len(originals), "forks & references"),
                  (sum(repo["stars"] for repo in originals), "stars on originals")]
        stats = "".join(f'<div class="stat-item"><strong>{number}</strong><span>{escape(label)}</span></div>' for number, label in values)
        cat_options = "".join(f'<option value="{key}">{escape(value["name"])}</option>' for key, value in categories.items())
        if any(not repo["fork"] and repo["name"] not in overrides for repo in repositories):
            cat_options += '<option value="other">More research</option>'
        languages = sorted({repo["language"] for repo in repositories})
        lang_options = "".join(f'<option value="{escape(language, quote=True)}">{escape(language)}</option>' for language in languages)
        rows = [repository_row(repo, overrides.get(repo["name"], {}), categories, featured)
                for repo in sorted(repositories, key=lambda repo: repo["updated"], reverse=True)]
        body = Template((ROOT / "portfolio/templates/index.html").read_text()).substitute(
            collections=collection_cards(categories, originals, overrides),
            stats=stats, featured_count=len(projects), featured="\n".join(feature_card(project, categories) for project in projects),
            research=research_tracks(focus, snapshot, names, replays), focus_reviewed=focus["reviewed_on"],
            category_options=cat_options, language_options=lang_options, total=len(repositories), repositories="\n".join(rows),
        )
        (stage / "index.html").write_text(render_base(body, "Hudson Forge | Independent research & engineering",
          "AI systems, quantum experiments, and tools that preserve the evidence behind a result. Explore the public work of Billy R. Davis Jr.", date, script="app.js"), encoding="utf-8")
        for index, project in enumerate(projects):
            next_project = projects[(index + 1) % len(projects)]
            comparison = ""
            if project.get("comparison"):
                cells = "".join(f'<tr><th scope="row">{escape(row["model"])}</th><td>{row["simulation"]}</td><td>{row["hardware"]}</td></tr>' for row in project["comparison"])
                comparison = f'<table class="evidence-table"><caption>Reported run-day test accuracy · two selected configurations</caption><thead><tr><th scope="col">Configuration</th><th scope="col">Simulation</th><th scope="col">Hardware</th></tr></thead><tbody>{cells}</tbody></table><p class="evidence-note">Read the paper for sampling uncertainty, controls, and the full tier comparison.</p>'
            values = {key: escape(project[key], quote=True) for key in
                      ("name", "label", "summary", "question", "finding", "scope")}
            replay = project.get("replay")
            if replay:
                replay_template = ROOT / "portfolio/templates" / replay["template"]
                transcript = project["links"][0]
                visual = Template(replay_template.read_text()).substitute(
                    transcript=html_link(transcript["label"], transcript["url"], "text-link"))
                primary_link = f'<a class="button primary" href="#replay">{escape(replay["action"])}</a>'
            else:
                image = escape(project["image"], quote=True)
                alt = escape(project["image_alt"], quote=True)
                visual = (f'<figure class="case-hero"><img src="../../{image}" alt="{alt}" width="1200" height="650">'
                          '<figcaption>Concept illustration · the linked repository contains the implementation and research artifacts.</figcaption></figure>')
                primary_link = html_link("Explore the repository", repo_url(project["repository"]), "button primary")
            values.update(category=escape(categories[project["category"]]["name"]), primary_link=primary_link, visual=visual,
                          first_link=html_link(project["links"][0]["label"], project["links"][0]["url"], "text-link"),
                          approach="".join(f"<li>{escape(item)}</li>" for item in project["approach"]), comparison=comparison,
                          links="".join(html_link(link["label"], link["url"]) for link in project["links"]),
                          next_slug=next_project["slug"], next_name=escape(next_project["name"]))
            page = Template((ROOT / "portfolio/templates/project.html").read_text()).substitute(values)
            destination = stage / "projects" / project["slug"]
            destination.mkdir(parents=True)
            (destination / "index.html").write_text(render_base(page, f'{project["name"]} | Hudson Forge',
                project["summary"], date, nested=True, script="replay.js" if replay else None), encoding="utf-8")
        not_found = '<section class="section-wrap case-header"><p class="eyebrow">404 / PAGE NOT FOUND</p><h1>Follow another thread.</h1><p class="case-summary">This page is not in the portfolio.</p><a class="button primary" href="./">Back to the collection →</a></section>'
        (stage / "404.html").write_text(render_base(not_found, "Page not found | Hudson Forge", "Return to the Hudson Forge project collection.", date), encoding="utf-8")
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    return {"repositories": len(repositories), "originals": len(originals), "featured": len(projects), "snapshot": date}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Fetch a fresh public snapshot before building")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if args.refresh:
        snapshot = refresh_snapshot()
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    else:
        snapshot = read_json(SNAPSHOT)
    print(json.dumps(build_site(snapshot, args.output.resolve())))


if __name__ == "__main__":
    main()
