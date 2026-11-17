"""Render the public GitHub profile's project updates."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import json
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


def github_json(path):
    request = Request(
        f"https://api.github.com/repos/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "Hudson-Forge-Profile-Updates",
        },
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


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


def render_markdown(updates):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    updates = sorted(
        (latest_update(project, repo) for project, repo in PROJECTS),
        key=lambda update: update.when,
        reverse=True,
    )
    readme = render_markdown(updates)
    card = render_card(updates[:3])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "README.md").write_text(readme, encoding="utf-8")
    (args.output_dir / "project-updates.svg").write_text(card, encoding="utf-8")


if __name__ == "__main__":
    main()
