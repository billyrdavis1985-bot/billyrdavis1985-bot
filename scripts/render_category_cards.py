"""Render the four GitHub collection cards at desktop and compact widths."""

from html import escape
from pathlib import Path


CARDS = (
    (
        "ai-agents", "AI & agents", ("AI & agents",),
        "Model orchestration and evaluation",
        '<path d="M34 36h16l12 16h14M34 68h16l12-16" />'
        '<circle cx="29" cy="36" r="5"/><circle cx="29" cy="68" r="5"/>'
        '<rect x="76" y="44" width="16" height="16" rx="5" class="accent"/>',
    ),
    (
        "quantum", "Quantum research", ("Quantum", "research"),
        "Hardware, drift, and error correction",
        '<ellipse cx="57" cy="52" rx="29" ry="12" transform="rotate(-36 57 52)"/>'
        '<ellipse cx="57" cy="52" rx="29" ry="12" transform="rotate(36 57 52)"/>'
        '<circle cx="57" cy="52" r="5" class="accent"/>',
    ),
    (
        "safety-data", "Safety & data", ("Safety & data",),
        "Document controls and injury research",
        '<path d="M57 26l23 9v16c0 13-9 23-23 30-14-7-23-17-23-30V35z"/>'
        '<path d="m46 52 8 8 15-16" class="accent"/>',
    ),
    (
        "tools", "Tools & foundations", ("Tools &", "foundations"),
        "Collectors, bridges, and reusable tools",
        '<rect x="35" y="31" width="44" height="42" rx="7"/>'
        '<path d="M44 44l10 8-10 8m16 0h10" class="accent"/>',
    ),
)


def render(title, lines, subtitle, symbol, compact=False):
    width, height = (300, 172) if compact else (600, 170)
    margin = 20 if compact else 30
    title_y = 54 if compact and len(lines) == 2 else 67
    font_size = 27 if compact else 34
    title_text = "".join(
        f'<text x="{margin}" y="{title_y + index * 32}">{escape(line)}</text>'
        for index, line in enumerate(lines)
    )
    description = "" if compact else (
        "\n  "
        f'<text x="{margin}" y="99" fill="#b9c6d3" font-size="17">{escape(subtitle)}</text>'
    )
    icon_transform = "translate(207 28) scale(.64)" if compact else "translate(446 15)"
    divider_y = height - 47
    arrow_x = width - margin - 20
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="system-ui,sans-serif">
  <title>{escape(title)}</title>
  <desc>{escape(subtitle)}</desc>
  <style>.accent {{ stroke: #a8dbe9; }}</style>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="15" fill="#0d1622" stroke="#405265" stroke-width="2"/>
  <g transform="{icon_transform}" fill="none" stroke="#e4aa7b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <rect x="5" y="1" width="104" height="102" rx="20" fill="#132333" stroke="#344b60" stroke-width="1.5"/>
    {symbol}
  </g>
  <g font-size="{font_size}" font-weight="700" fill="#f0f4f9">{title_text}</g>
{description}
  <path d="M{margin} {divider_y}H{width - margin}" stroke="#2e3e50"/>
  <text x="{margin}" y="{height - 18}" fill="#edb483" font-size="16" font-weight="600">Open collection</text>
  <path d="M{arrow_x} {height - 24}h20m-7-7 7 7-7 7" fill="none" stroke="#edb483" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''


def main():
    destination = Path(__file__).resolve().parents[1] / "assets" / "categories"
    destination.mkdir(parents=True, exist_ok=True)
    for slug, title, compact_lines, subtitle, symbol in CARDS:
        for compact, lines in ((False, (title,)), (True, compact_lines)):
            suffix = "-compact" if compact else ""
            (destination / f"{slug}{suffix}.svg").write_text(
                render(title, lines, subtitle, symbol, compact), encoding="utf-8"
            )


if __name__ == "__main__":
    main()
