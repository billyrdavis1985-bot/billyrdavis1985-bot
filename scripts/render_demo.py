"""Render the profile's demo playback and project map.

Requires Pillow 13.0.0. Run from the profile repository root with
python3 scripts/render_demo.py. The captured CLI output is checked before
any demo images are written.
"""

from dataclasses import dataclass
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
SOURCE_COMMIT = "fc771b36b16a49915c07891673fc4bc5ead9b3c8"
BACKGROUND = "#0b1420"
PANEL = "#111f2e"
TEXT = "#eef3f7"
MUTED = "#b2c1d0"
COPPER = "#edb483"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


@dataclass(frozen=True)
class Scene:
    title: str
    subtitle: str
    color: str
    lines: tuple[str, ...]


def captured_line(lines, prefix):
    matches = [line for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one captured line beginning {prefix!r}")
    return matches[0]


def read_scenes():
    lines = (ROOT / "docs/forgevigil-demo.txt").read_text(encoding="utf-8").splitlines()
    captured_line(lines, "ForgeVigil smoke demo - fixture assessor, no inference, temporary synthetic state")
    if captured_line(lines, "RESULT: ") != "RESULT: PASS":
        raise ValueError("The captured demo did not pass")

    scenes = []
    for verdict, subtitle, color in (
        ("ALLOW", "Approved public document", "#88dbb2"),
        ("DENY", "Restricted document", "#f0a8a5"),
        ("REVIEW", "Unverified approval", "#edc47e"),
    ):
        summary = captured_line(lines, f"[{verdict} case] ")
        match = re.fullmatch(
            rf"\[{verdict} case\] HTTP (\d+) disposition={verdict} "
            r"reason=([A-Z_]+) delivered=(True|False)",
            summary,
        )
        if match is None:
            raise ValueError(f"Unexpected captured case output: {summary}")
        status, reason, delivered = match.groups()
        scenes.append(Scene(verdict, subtitle, color, (
            f"HTTP {status}",
            f"disposition={verdict}",
            f"reason={reason}",
            f"delivered={delivered}",
        )))

    replay = captured_line(lines, "[replay of ALLOW case] ")
    if "outcome=replayed (no new assessment or delivery)" not in replay:
        raise ValueError("The captured replay did not produce the expected outcome")
    scenes.append(Scene("REPLAYED", "Repeat the approved request", "#90d2e3", (
        "HTTP 200",
        "outcome=replayed",
        "no new assessment or delivery",
    )))

    release = captured_line(lines, "[operator release of REVIEW case] ")
    if "released by demo-operator, scope re-check passed," not in release:
        raise ValueError("The scripted release did not pass its scope recheck")
    released_replay = captured_line(lines, "[replay of REVIEW case] ")
    if "delivered=True review=release" not in released_replay:
        raise ValueError("The released request was not replayed as expected")
    scenes.append(Scene("LOCAL RELEASE", "Scripted operator action", "#edb483", (
        "released by demo-operator",
        "scope re-check passed",
        "delivered=True review=release",
    )))

    outbox = captured_line(lines, "outbox items: ")
    if outbox != "outbox items: 2 (expected 2; only approved public-spec bytes: True)":
        raise ValueError("The captured outbox did not contain the expected items")
    captured_line(lines, "temporary demo state removed")
    scenes.append(Scene("RESULT: PASS", "Final outbox and cleanup", "#88dbb2", (
        "outbox items: 2 (expected 2)",
        "only approved public-spec bytes: True",
        "temporary demo state removed",
    )))
    return scenes


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def render_scene(scene, index, total):
    image = Image.new("RGB", (840, 450), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((30, 22), "ForgeVigil", font=font("DejaVuSans-Bold.ttf", 29), fill=TEXT)
    draw.text((610, 30), "OFFLINE FIXTURE", font=font("DejaVuSans.ttf", 19), fill=COPPER)
    draw.text((30, 70), "Recorded CLI output · fictional cases", font=font("DejaVuSans.ttf", 19), fill=MUTED)
    draw.line((30, 107, 810, 107), fill="#304152", width=1)
    draw.text((30, 126), scene.title, font=font("DejaVuSans-Bold.ttf", 38), fill=scene.color)
    draw.text((30, 176), scene.subtitle, font=font("DejaVuSans.ttf", 21), fill=MUTED)
    draw.rounded_rectangle((30, 215, 810, 370), radius=10, fill=PANEL, outline="#344554")
    for line_index, line in enumerate(scene.lines):
        draw.text((50, 230 + 31 * line_index), line, font=font("DejaVuSansMono.ttf", 20), fill=TEXT)
    draw.text((30, 390), f"Source {SOURCE_COMMIT[:7]} · full transcript linked below", font=font("DejaVuSans.ttf", 17), fill=MUTED)
    for step in range(total):
        left = 30 + 130 * step
        draw.rounded_rectangle((left, 427, left + 116, 431), radius=2, fill=scene.color if step == index else "#304152")
    return image


def render_project_map():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="840" height="520" viewBox="0 0 840 520" font-family="system-ui, sans-serif">
  <title>Hudson Forge public project map</title>
  <desc>HF-IQR benchmark research informs HF Critic. Forge Agent evaluates local reasoning critics. ForgeVigil, QNN-P1, and WIPS are parallel application and research tracks.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#edb483"/>
    </marker>
  </defs>
  <rect x="1" y="1" width="838" height="518" rx="14" fill="#0b1420" stroke="#405366"/>
  <text x="28" y="44" fill="#eef3f7" font-size="27" font-weight="700">How the projects connect</text>
  <text x="28" y="81" fill="#edb483" font-size="20">Reasoning research and evaluation</text>
  <g fill="#111f2e" stroke="#405366">
    <rect x="28" y="139" width="232" height="104" rx="10"/>
    <rect x="304" y="139" width="232" height="104" rx="10"/>
    <rect x="580" y="139" width="232" height="104" rx="10"/>
  </g>
  <g fill="#eef3f7" font-size="24" font-weight="700" text-anchor="middle">
    <text x="144" y="181">HF-IQR V1–V3</text>
    <text x="420" y="181">HF Critic</text>
    <text x="696" y="181">Forge Agent</text>
  </g>
  <g fill="#b2c1d0" font-size="18" text-anchor="middle">
    <text x="144" y="216">Benchmark studies</text>
    <text x="420" y="216">Local reasoning critics</text>
    <text x="696" y="216">Governed evaluation</text>
  </g>
  <g stroke="#edb483" stroke-width="2" fill="none" marker-end="url(#arrow)">
    <path d="M260 191 H303"/>
    <path d="M536 191 H579"/>
  </g>
  <g fill="#edb483" font-size="16" text-anchor="middle">
    <text x="282" y="113">Research lineage</text>
    <text x="558" y="113">Critic evaluation</text>
  </g>
  <path d="M28 280 H812" stroke="#304152"/>
  <text x="28" y="320" fill="#edb483" font-size="20">Application and hardware research tracks</text>
  <g fill="#111f2e" stroke="#405366">
    <rect x="28" y="346" width="232" height="104" rx="10"/>
    <rect x="304" y="346" width="232" height="104" rx="10"/>
    <rect x="580" y="346" width="232" height="104" rx="10"/>
  </g>
  <g fill="#eef3f7" font-size="24" font-weight="700" text-anchor="middle">
    <text x="144" y="388">ForgeVigil</text>
    <text x="420" y="388">QNN-P1</text>
    <text x="696" y="388">WIPS</text>
  </g>
  <g fill="#b2c1d0" font-size="18" text-anchor="middle">
    <text x="144" y="423">Document controls</text>
    <text x="420" y="423">Quantum hardware</text>
    <text x="696" y="423">Manufacturing safety</text>
  </g>
  <text x="28" y="491" fill="#b2c1d0" font-size="17">Source notes and repository links accompany this map.</text>
</svg>
"""


def main():
    scenes = read_scenes()
    frames = [render_scene(scene, index, len(scenes)) for index, scene in enumerate(scenes)]
    output = ROOT / "assets/demos"
    output.mkdir(parents=True, exist_ok=True)
    frames[0].save(output / "forgevigil-demo.png", optimize=True)
    color_sample = Image.new("RGB", (840, 450 * len(frames)))
    for index, frame in enumerate(frames):
        color_sample.paste(frame, (0, 450 * index))
    palette = color_sample.quantize(colors=96)
    animation = [frame.quantize(palette=palette) for frame in frames]
    animation[0].save(
        output / "forgevigil-demo.gif",
        save_all=True,
        append_images=animation[1:],
        duration=[2200, 2200, 2400, 2400, 2600, 3000],
        loop=0,
        optimize=True,
    )
    (ROOT / "assets/project-map.svg").write_text(render_project_map(), encoding="utf-8")


if __name__ == "__main__":
    main()
