"""Render the public GitHub profile's project updates."""

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
    project: str
    repository: str
    language: str
    stars: int


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
        f"https://api.github.com/repos/{path}",
        headers=headers,
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def repository_stats(project, repo):
    metadata = github_json(f"{OWNER}/{repo}")
    if metadata["private"]:
        raise ValueError(f"The featured repository {repo} is no longer public")
    return RepositoryStats(
        project,
        repo,
        metadata["language"] or "Unspecified",
        metadata["stargazers_count"],
    )


def latest_update(project, repo):
    repository = f"{OWNER}/{repo}"
    github_url = f"https://github.com/{repository}"
    releases = github_json(f"{repository}/releases?per_page=1")
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

    entry = github_json(f"{repository}/commits?per_page=1")[0]
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
        f"Public GitHub metadata checked {refreshed} UTC for the six featured repositories.",
        "",
        "| Project | Primary language | Stars |",
        "| --- | --- | --- |",
    ))
    for item in stats:
        language = escape(item.language).replace("|", r"\|")
        lines.append(
            f"| [{item.project}](https://github.com/{OWNER}/{item.repository}) "
            f"| {language} | {item.stars:,} |"
        )
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
    counts = Counter(item.language for item in stats)
    languages = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    height = max(260, 120 + 46 * len(languages))
    colors = ("#edb483", "#90d2e3", "#bdc9d4", "#88dbb2", "#c2a2d9", "#e6c778")
    rows = []
    for index, (language, count) in enumerate(languages):
        y = 98 + 46 * index
        color = colors[index % len(colors)]
        rows.append(
            f'  <circle cx="389" cy="{y - 6}" r="5" fill="{color}"/>\n'
            f'  <text x="404" y="{y}" fill="#eef3f7" font-size="19">{escape(language)}</text>\n'
            f'  <text x="718" y="{y}" fill="#edb483" font-size="19" text-anchor="end">{count}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="{height}" '
        f'viewBox="0 0 760 {height}" font-family="system-ui, sans-serif">\n'
        "  <title>Featured public repository statistics</title>\n"
        f'  <desc>{len(stats)} featured repositories and {sum(item.stars for item in stats)} '
        f'GitHub stars. Metadata refreshed {refreshed} UTC.</desc>\n'
        f'  <rect x="1" y="1" width="758" height="{height - 2}" rx="12" fill="#0b1420" stroke="#405366"/>\n'
        f'  <path d="M354 24 V{height - 48}" stroke="#304152"/>\n'
        '  <text x="24" y="42" fill="#edb483" font-size="20">Featured public projects</text>\n'
        f'  <text x="24" y="104" fill="#eef3f7" font-size="43" font-weight="700">{len(stats)}</text>\n'
        '  <text x="24" y="130" fill="#bdc9d4" font-size="18">repositories</text>\n'
        f'  <text x="24" y="185" fill="#eef3f7" font-size="43" font-weight="700">{sum(item.stars for item in stats):,}</text>\n'
        '  <text x="24" y="210" fill="#bdc9d4" font-size="18">GitHub stars</text>\n'
        '  <text x="380" y="42" fill="#edb483" font-size="20">Primary language by repository</text>\n'
        + "\n".join(rows)
        + f'\n  <text x="24" y="{height - 18}" fill="#bdc9d4" font-size="16">Metadata refreshed {refreshed} UTC</text>\n'
        "</svg>\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    updates = sorted(
        (latest_update(project, repo) for project, repo in PROJECTS),
        key=lambda update: update.when,
        reverse=True,
    )
    stats = [repository_stats(project, repo) for project, repo in PROJECTS]
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
