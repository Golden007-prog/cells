#!/usr/bin/env python3
"""Render a reproducible animated GIF from real simulation frames (Pillow)."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cells import Ink, PALETTES, STEP, World, render
from preview import xterm_hex


def main() -> None:
    from PIL import Image, ImageDraw, ImageFont

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "docs/demo.gif"
    )
    cli.add_argument("--font", type=Path, help="Path to a monospace TrueType font")
    cli.add_argument("--seed", type=int, default=12)
    cli.add_argument(
        "--symbol-font", type=Path, help="Fallback TrueType font for Runic phage glyphs"
    )
    args = cli.parse_args()
    candidates = ([args.font] if args.font else []) + [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        Path("/System/Library/Fonts/Menlo.ttc"),
    ]
    if args.font and not args.font.is_file():
        cli.error("--font must name an existing font file")
    font_path = next((p for p in candidates if p.is_file()), None)
    font = ImageFont.truetype(str(font_path), 13) if font_path else ImageFont.load_default()
    if args.symbol_font and not args.symbol_font.is_file():
        cli.error("--symbol-font must name an existing font file")
    symbol_candidates = ([args.symbol_font] if args.symbol_font else []) + [
        Path("/usr/share/fonts/truetype/noto/NotoSansRunic-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeMono.ttf"),
    ]
    symbol_path = next((p for p in symbol_candidates if p.is_file()), None)
    symbol_font = ImageFont.truetype(str(symbol_path), 13) if symbol_path else font
    background = "#10171d"
    colors = {ink: xterm_hex(color[0]) for ink, color in zip(Ink, PALETTES["slide"])}
    palette = []
    base = tuple(int(background[i : i + 2], 16) for i in (1, 3, 5))
    palette.extend(base)
    for color in colors.values():
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        for weight in (0.35, 0.6, 0.8, 1):
            palette.extend(round(a * (1 - weight) + b * weight) for a, b in zip(base, rgb))
    palette.extend([0] * (768 - len(palette)))
    reference = Image.new("P", (1, 1))
    reference.putpalette(palette)
    world = World(100, 32, args.seed)
    frames = []
    for index in range(120):  # 15 seconds at 8 fps, five simulation seconds per second.
        at = index * 5 / 8
        while world.time + 1e-8 < at:
            world.update(STEP)
        frame = render(world, True)
        picture = Image.new("RGB", (832, 568), background)
        draw = ImageDraw.Draw(picture)
        for y, row in enumerate(frame.pixels):
            for x, pixel in enumerate(row):
                if pixel.char != " ":
                    draw.text(
                        (16 + x * 8, 12 + y * 16),
                        pixel.char,
                        font=symbol_font if pixel.char in "ᛘᛦ" else font,
                        fill=colors[pixel.ink],
                    )
        draw.text(
            (16, 542),
            f"cells / seed {args.seed}    Space pause    ? help    q quit",
            font=font,
            fill="#97a5b0",
        )
        frames.append(picture.quantize(palette=reference, dither=Image.Dither.NONE))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # GIF delays use 10 ms units; alternate to retain an exact 8 fps average.
    delays = [120 if i % 2 == 0 else 130 for i in range(len(frames))]
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=delays,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"{args.output} ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
