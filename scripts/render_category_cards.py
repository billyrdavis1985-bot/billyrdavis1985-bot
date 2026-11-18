"""Render the profile's four matching SVG navigation illustrations."""

from html import escape
from pathlib import Path


CARDS = (
    ("ai-agents", "AI & agents", "Reasoning, models, evaluation", "01", """
      <path d="M420 69 469 42 525 64 548 112 508 151 451 145 409 112 420 69 508 151 469 42 451 145 525 64 409 112 548 112 420 69" fill="none" stroke="#aa7454" stroke-width="2"/>
      <path d="M420 69 484 96 525 64 M451 145 484 96 548 112 M469 42 484 96 508 151 M409 112 484 96" fill="none" stroke="#90d2e3" stroke-width="1.4" opacity=".8"/>
      <g fill="#edb483" stroke="#5e4435" stroke-width="2">
        <circle cx="420" cy="69" r="8"/><circle cx="469" cy="42" r="7"/>
        <circle cx="525" cy="64" r="9"/><circle cx="548" cy="112" r="7"/>
        <circle cx="508" cy="151" r="8"/><circle cx="451" cy="145" r="7"/>
        <circle cx="409" cy="112" r="6"/>
      </g><circle cx="484" cy="96" r="17" fill="#172b3a" stroke="#90d2e3" stroke-width="3"/>
      <circle cx="484" cy="96" r="6" fill="#c6edf4"/>
    """),
    ("quantum", "Quantum research", "Hardware, drift, error correction", "02", """
      <path d="m419 76 61-35 61 35v70l-61 35-61-35z M419 76l61 35 61-35 M480 111v70 M480 41v70 M419 146l61-35 61 35" fill="none" stroke="#bd8b67" stroke-width="2.4"/>
      <ellipse cx="480" cy="111" rx="87" ry="31" transform="rotate(-28 480 111)" fill="none" stroke="#90d2e3" stroke-width="1.5" opacity=".8"/>
      <g fill="#edb483" stroke="#694b37" stroke-width="2">
        <circle cx="419" cy="76" r="7"/><circle cx="480" cy="41" r="8"/>
        <circle cx="541" cy="76" r="7"/><circle cx="419" cy="146" r="7"/>
        <circle cx="480" cy="181" r="8"/><circle cx="541" cy="146" r="7"/>
      </g><circle cx="480" cy="111" r="12" fill="#c7eaf1"/>
      <circle cx="557" cy="79" r="5" fill="#90d2e3"/>
    """),
    ("safety-data", "Safety & data", "Document controls, injury research", "03", """
      <g fill="none" stroke="#4c6677" stroke-width="1.4" opacity=".6">
        <path d="M401 57h150v108H401z M401 84h150 M401 111h150 M401 138h150 M431 57v108 M461 57v108 M491 57v108 M521 57v108"/>
      </g>
      <path d="m444 37 65 20v45c0 39-24 61-65 83-40-22-64-44-64-83V57z" fill="#122535" stroke="#edb483" stroke-width="3"/>
      <path d="m444 54 48 15v33c0 29-18 48-48 65-29-17-47-36-47-65V69z" fill="#1b3140" stroke="#815c43"/>
      <path d="m420 108 16 16 33-38" fill="none" stroke="#90d2e3" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <g fill="#edb483"><rect x="520" y="113" width="9" height="43" rx="2"/><rect x="536" y="92" width="9" height="64" rx="2"/><rect x="552" y="70" width="9" height="86" rx="2"/></g>
    """),
    ("tools", "Tools & foundations", "Collectors, bridges, reusable tools", "04", """
      <path d="M395 70h35V44h88v26h38 M395 143h35v27h88v-27h38 M406 108h142 M473 28v161" fill="none" stroke="#516b7b" stroke-width="2"/>
      <g fill="#152c3c" stroke="#b78863" stroke-width="2">
        <path d="m418 75 31-18 32 18v37l-32 18-31-18z"/>
        <path d="m482 75 31-18 32 18v37l-32 18-31-18z"/>
        <path d="m450 130 31-18 32 18v37l-32 18-31-18z"/>
      </g>
      <path d="m418 75 31 18 32-18 M449 93v37 M482 75l31 18 32-18 M513 93v37 M450 130l31 18 32-18 M481 148v37" fill="none" stroke="#edb483" stroke-width="2"/>
      <g fill="#90d2e3"><circle cx="395" cy="70" r="4"/><circle cx="395" cy="143" r="4"/><circle cx="556" cy="70" r="4"/><circle cx="556" cy="143" r="4"/></g>
    """),
)


def render(title, subtitle, number, illustration):
    font_size = 33 if len(title) > 15 else 38
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="240" viewBox="0 0 600 240" font-family="system-ui,sans-serif">
  <title>Explore {escape(title)}</title>
  <desc>{escape(subtitle)}. A decorative illustration accompanies this category.</desc>
  <defs><radialGradient id="halo"><stop stop-color="#a36c43" stop-opacity=".22"/><stop offset="1" stop-color="#0b1420" stop-opacity="0"/></radialGradient></defs>
  <rect x="1" y="1" width="598" height="238" rx="14" fill="#0b1420" stroke="#405366"/>
  <ellipse cx="481" cy="101" rx="119" ry="110" fill="url(#halo)"/>
  <path d="M26 181h327 M26 23v120" stroke="#304152"/>
  <text x="41" y="43" fill="#edb483" font-size="13" letter-spacing="2">{number} / EXPLORE</text>
  <text x="41" y="113" fill="#eef3f7" font-size="{font_size}" font-weight="700">{escape(title)}</text>
  <text x="41" y="148" fill="#bdc9d4" font-size="16">{escape(subtitle)}</text>
  {illustration}
  <text x="41" y="213" fill="#edb483" font-size="15">Open the collection</text>
  <path d="M540 207h26m-8-8 8 8-8 8" fill="none" stroke="#edb483" stroke-width="2"/>
</svg>
'''


def main():
    destination = Path(__file__).resolve().parents[1] / "assets" / "categories"
    destination.mkdir(parents=True, exist_ok=True)
    for slug, title, subtitle, number, illustration in CARDS:
        (destination / f"{slug}.svg").write_text(render(title, subtitle, number, illustration), encoding="utf-8")
        lines = {"ai-agents": ("AI &", "agents"), "quantum": ("Quantum", "research"),
                 "safety-data": ("Safety &", "data"), "tools": ("Tools &", "foundations")}[slug]
        compact = f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="240" viewBox="0 0 300 240" font-family="system-ui,sans-serif">
  <title>Explore {escape(title)}</title>
  <desc>{escape(subtitle)}. Compact category navigation.</desc>
  <rect x="1" y="1" width="298" height="238" rx="14" fill="#0b1420" stroke="#405366"/>
  <text x="22" y="30" fill="#edb483" font-size="11" letter-spacing="1">{number} / EXPLORE</text>
  <g transform="translate(43 -7) scale(.4)">{illustration}</g>
  <text x="22" y="114" fill="#eef3f7" font-size="32" font-weight="700">{escape(lines[0])}</text>
  <text x="22" y="153" fill="#eef3f7" font-size="32" font-weight="700">{escape(lines[1])}</text>
  <path d="M22 183h256" stroke="#304152"/>
  <text x="22" y="214" fill="#edb483" font-size="15">Open collection</text>
  <path d="M252 208h22m-7-7 7 7-7 7" fill="none" stroke="#edb483" stroke-width="2"/>
</svg>
'''
        (destination / f"{slug}-compact.svg").write_text(compact, encoding="utf-8")


if __name__ == "__main__":
    main()
