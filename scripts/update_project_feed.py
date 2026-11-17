"""Render featured updates and a complete inventory of public repositories."""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from urllib.request import Request, urlopen


OWNER = "billyrdavis1985-bot"
PROJECTS = (
    ("ForgeVigil", "ForgeVigil"),
    ("Forge Agent", "forge-agent"),
    ("HF Critic", "hf-critic"),
    ("HF-IQR V3", "HF-IQR-V3"),
    ("QNN-P1", "IRMB_QNN-P1_DriftArchive_HardwareValidation"),
    ("WIPS", "WIPS-Preflight-OSHA-2024"),
)


@dataclass(frozen=True)
class Update:
    project: str
    kind: str
    when: datetime
    title: str
    url: str


@dataclass(frozen=True)
class RepositoryStats:
    repository: str
    language: str
    stars: int
    fork: bool
    archived: bool


def github_json(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "Hudson-Forge-Profile-Updates",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"https://api.github.com/{path}",
        headers=headers,
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def public_repository_stats():
    """Paginate the public user endpoint, including forks and archived projects."""
    repositories = {}
    page = 1
    while True:
        batch = github_json(
            f"users/{OWNER}/repos?type=owner&sort=full_name&per_page=100&page={page}"
        )
        for metadata in batch:
            if (metadata["private"]
                    or metadata.get("visibility", "public") != "public"
                    or metadata["owner"]["login"].lower() != OWNER.lower()):
                continue
            repositories[metadata["name"]] = RepositoryStats(
                metadata["name"], metadata["language"] or "Unspecified",
                metadata["stargazers_count"], metadata["fork"], metadata["archived"],
            )
        if len(batch) < 100:
            break
        page += 1
    if not repositories:
        raise ValueError("GitHub returned no public repositories")
    return sorted(repositories.values(), key=lambda item: item.repository.lower())


def latest_update(project, repo):
    repository = f"{OWNER}/{repo}"
    github_url = f"https://github.com/{repository}"
    releases = github_json(f"repos/{repository}/releases?per_page=1")
    if releases:
        release = releases[0]
        tag = release["tag_name"]
        return Update(
            project,
            "Pre-release" if release["prerelease"] else "Release",
            datetime.fromisoformat(release["published_at"]),
            release["name"] or tag,
            f"{github_url}/releases/tag/{quote(tag, safe='')}",
        )

    entry = github_json(f"repos/{repository}/commits?per_page=1")[0]
    commit = entry["commit"]
    messages = [line.strip() for line in commit["message"].splitlines() if line.strip()]
    title = messages[0] if messages else "View commit"
    if title.startswith("Merge pull request #") and len(messages) > 1:
        title = messages[1]
    return Update(
        project,
        "Commit",
        datetime.fromisoformat(commit["committer"]["date"]),
        title,
        f"{github_url}/commit/{entry['sha']}",
    )


def clean_title(title):
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", title).split())


def render_markdown(updates, stats, refreshed):
    lines = [
        "# Latest project updates",
        "",
        "One entry per project. GitHub releases take precedence when available. "
        "Otherwise the entry shows the latest commit on the default branch.",
        "",
    ]
    for update in updates:
        date = update.when.astimezone(timezone.utc).date()
        title = re.sub(r"([\\\[\]*_#\x60])", r"\\\1", escape(clean_title(update.title)))
        lines.append(f"- **{update.project}** · {date} · {update.kind} · [{title}]({update.url})")
    lines.extend((
        "",
        "## Repository statistics",
        "",
        f"Public GitHub metadata checked {refreshed} UTC. All public repositories owned by {OWNER} "
        "are included, including forks and archived projects. Private repositories are excluded.",
    ))
    originals = [item for item in stats if not item.fork]
    forks = [item for item in stats if item.fork]
    lines.extend((
        "",
        f"**{len(stats)} public repositories · {len(originals)} originals · {len(forks)} forks · "
        f"{sum(item.stars for item in originals)} stars on originals**",
        "",
        "Original means GitHub does not mark the repository as a fork. Language counts use one "
        "primary language per original repository, rather than source-code byte percentages. "
        "Unspecified means GitHub has not detected a primary language.",
    ))
    for title, group in (("Original repositories", originals), ("Forks", forks)):
        lines.extend(("", f"### {title}", "", "| Repository | Primary language | Stars | Archived |",
                      "| --- | --- | --- | --- |"))
        for item in group:
            name = re.sub(r"([\\\[\]*_`])", r"\\\1", escape(item.repository)).replace("|", r"\|")
            language = escape(item.language).replace("|", r"\|")
            lines.append(
                f"| [{name}](https://github.com/{OWNER}/{quote(item.repository, safe='')}) "
                f"| {language} | {item.stars:,} | {'Yes' if item.archived else 'No'} |"
            )
    lines.extend(("", "## Contribution skyline", "",
                  "The animated skyline uses the public profile calendar. Each building represents a day. "
                  "Height follows log(1 + daily contributions); roof color follows GitHub's activity level. "
                  "The moving light is decorative and does not change the data.", "",
                  "[Calendar data and refresh date](contributions.json) · "
                  "[Static skyline](contribution-skyline-static.svg) · "
                  f"[Source and limitations](https://github.com/{OWNER}/{OWNER}/blob/main/docs/profile-visuals.md)"))
    return "\n".join(lines) + "\n"


def render_card(updates):
    width = 560
    height = 12 + 64 * len(updates)
    rows = []
    for index, update in enumerate(updates):
        y = 33 + 64 * index
        date = update.when.astimezone(timezone.utc).date()
        subject = f"{update.kind} · {clean_title(update.title)}"
        if len(subject) > 56:
            subject = subject[:55].rstrip() + "…"
        rows.append(
            f'  <text x="20" y="{y}" fill="#f8fafc" font-size="21" '
            f'font-weight="700">{escape(update.project)}</text>\n'
            f'  <text x="540" y="{y}" text-anchor="end" fill="#f4ac75" '
            f'font-size="17">{date}</text>\n'
            f'  <text x="20" y="{y + 23}" fill="#bdc9d4" font-size="15" '
            f'font-family="monospace">{escape(subject)}</text>'
        )
    body = "\n".join(rows)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="system-ui, sans-serif">\n'
        "  <title>Latest Hudson Forge project updates</title>\n"
        f'  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" '
        'fill="#111922" stroke="#5c493e" stroke-width="2"/>\n'
        f"{body}\n"
        "</svg>\n"
    )


def render_stats_card(stats, refreshed):
    originals = [item for item in stats if not item.fork]
    counts = Counter(item.language for item in originals)
    languages = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    height = 380 + 32 * max(0, len(languages) - 3)
    colors = ("#edb483", "#90d2e3", "#bdc9d4", "#88dbb2", "#c2a2d9", "#e6c778")
    rows = []
    bar_x = 28
    for index, (language, count) in enumerate(languages):
        y = 268 + 32 * index
        color = colors[index % len(colors)]
        bar_width = 704 * count / max(1, len(originals))
        rows.append(
            f'  <rect x="{bar_x:.2f}" y="224" width="{bar_width:.2f}" height="8" fill="{color}"/>\n'
            f'  <circle cx="34" cy="{y - 6}" r="4" fill="{color}"/>\n'
            f'  <text x="48" y="{y}" fill="#eef3f7" font-size="17">{escape(language)}</text>\n'
            f'  <text x="730" y="{y}" fill="{color}" font-size="17" text-anchor="end">{count} repositories</text>'
        )
        bar_x += bar_width
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" '
        f'viewBox="0 0 760 {height}" font-family="system-ui, sans-serif">\n'
        "  <title>All public repository statistics</title>\n"
        f'  <desc>{len(stats)} public repositories, {len(originals)} originals, '
        f'{len(stats) - len(originals)} forks and {sum(item.stars for item in originals)} stars on originals. '
        f'Metadata refreshed {refreshed} UTC.</desc>\n'
        f'  <rect x="1" y="1" width="758" height="{height - 2}" rx="12" fill="#0b1420" stroke="#405366"/>\n'
        '  <text x="28" y="36" fill="#edb483" font-size="15" letter-spacing="2">THE PUBLIC WORKBENCH</text>\n'
        f'  <text x="28" y="91" fill="#eef3f7" font-size="43" font-weight="700">{len(originals)} original projects</text>\n'
        '  <path d="M28 114 H732" stroke="#304152"/>\n'
        f'  <text x="28" y="157" fill="#eef3f7" font-size="30" font-weight="700">{len(stats)}</text>\n'
        '  <text x="28" y="181" fill="#bdc9d4" font-size="16">public repositories</text>\n'
        f'  <text x="288" y="157" fill="#90d2e3" font-size="30" font-weight="700">{len(stats) - len(originals)}</text>\n'
        '  <text x="288" y="181" fill="#bdc9d4" font-size="16">forks</text>\n'
        f'  <text x="520" y="157" fill="#edb483" font-size="30" font-weight="700">{sum(item.stars for item in originals):,}</text>\n'
        '  <text x="520" y="181" fill="#bdc9d4" font-size="16">stars on originals</text>\n'
        '  <text x="28" y="212" fill="#bdc9d4" font-size="15">Primary languages · original repositories</text>\n'
        + "\n".join(rows)
        + f'\n  <text x="24" y="{height - 18}" fill="#bdc9d4" font-size="16">Metadata refreshed {refreshed} UTC</text>\n'
        "</svg>\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    stats = public_repository_stats()
    public_names = {item.repository for item in stats}
    if any(repo not in public_names for _, repo in PROJECTS):
        raise ValueError("A featured project is no longer in the public repository inventory")
    updates = sorted(
        (latest_update(project, repo) for project, repo in PROJECTS),
        key=lambda update: update.when,
        reverse=True,
    )
    refreshed = datetime.now(timezone.utc).date()
    readme = render_markdown(updates, stats, refreshed)
    card = render_card(updates[:3])
    stats_card = render_stats_card(stats, refreshed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "README.md").write_text(readme, encoding="utf-8")
    (args.output_dir / "project-updates.svg").write_text(card, encoding="utf-8")
    (args.output_dir / "project-stats.svg").write_text(stats_card, encoding="utf-8")


if __name__ == "__main__":
    main()

