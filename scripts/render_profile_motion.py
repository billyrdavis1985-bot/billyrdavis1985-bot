"""Render the GitHub introduction GIFs from the checked-in artwork.

Run with Pillow installed. The GIFs play once and leave a readable final frame.
"""

import argparse
from math import exp, pi, sin
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "assets" / "hudson-forge-banner.webp"
OUTPUT = ROOT / "assets" / "motion"


def circuit_banner():
    with Image.open(ART) as artwork:
        base = artwork.convert("RGB").resize((864, 288), Image.Resampling.LANCZOS)
    base.info.clear()

    # Animate only the board so the wordmark and its background stay still.
    board_left = 528
    board = base.crop((board_left, 0, base.width, base.height))
    luminance = ImageOps.grayscale(board).point(lambda value: min(255, round(value * 1.6)))
    dimensions = [(x, y) for y in range(board.height) for x in range(board.width)]
    frames = [base]
    for frame in range(1, 25):
        phase = frame / 25
        sweep_center = -65 + (board.width + 235) * phase
        strength = sin(pi * phase) * 0.68
        sweep = Image.new("L", board.size)
        sweep.putdata([
            round(255 * strength * min(1, x / 45)
                  * exp(-((x + y * .32 - sweep_center) / 53) ** 2))
            for x, y in dimensions
        ])
        glow = ImageChops.multiply(sweep, luminance)
        warm = Image.new("RGB", board.size, (244, 156, 82))
        lit = Image.composite(ImageChops.screen(board, warm), board, glow)
        composed = base.copy()
        composed.paste(lit, (board_left, 0))
        frames.append(composed)

    # A common palette keeps dark artwork stable between frames and allows GIF deltas.
    swatches = Image.new("RGB", (base.width, base.height * 4))
    for index, frame in enumerate((base, frames[7], frames[13], frames[19])):
        swatches.paste(frame, (0, index * base.height))
    palette = swatches.quantize(colors=256)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    indexed[0].save(OUTPUT / "circuit-banner.gif", save_all=True,
                    append_images=[*indexed[1:], indexed[0]], duration=[260] + [120] * 24 + [700],
                    optimize=True, disposal=1)


def greeting(mono_font):
    command = "./welcome"
    height = 111
    title_font = ImageFont.truetype(mono_font, 33)
    prompt_font = ImageFont.truetype(mono_font, 24)

    def render(prompt, cursor):
        frame = Image.new("RGB", (700, height), "#0d1622")
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((1, 1, 698, height - 2), radius=14,
                               fill="#0d1622", outline="#405265", width=2)
        draw.text((25, 17), "$", font=prompt_font, fill="#a8dbe9")
        draw.text((52, 17), prompt, font=prompt_font, fill="#edb483")
        if cursor:
            x = 55 + round(draw.textlength(prompt, font=prompt_font))
            draw.rectangle((x, 22, x + 11, 38), fill="#edb483")
        draw.text((25, 56), "Hi, I’m Billy R. Davis Jr.", font=title_font, fill="#f0f4f9")
        return frame

    still = render(command, False)
    still.save(OUTPUT / "greeting.png", optimize=True)
    palette = render(command, True).quantize(colors=128)
    frames = [render(command[:index], True).quantize(palette=palette, dither=Image.Dither.NONE)
              for index in range(len(command) + 1)]
    frames[0].save(OUTPUT / "greeting.gif", save_all=True,
                   append_images=[*frames[1:], still.quantize(palette=palette, dither=Image.Dither.NONE)],
                   duration=[180] + [110] * len(command) + [650],
                   optimize=True, disposal=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mono-font", default="DejaVuSansMono.ttf")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    circuit_banner()
    greeting(args.mono_font)


if __name__ == "__main__":
    main()
