#!/usr/bin/env python3
"""Generate tool previews from real intervention states and the normal renderer."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terminal_cells import World, Cell, Drifter, Bacterium, Frame, render, STEP  # noqa: E402
from terminal_cells.lab import Target  # noqa: E402
from preview import atlas


def main():
    panels = []
    for kind, at, label in [
        ("cell", 0, "Lyse / immediate rupture"),
        ("cell", 2.2, "Lyse / organelles disperse"),
        ("red", 2.2, "Red cell / fading membrane ghost"),
        ("fluid", 0.5, "Feed and Stir / local droplet and current"),
    ]:
        world = World(120, 40, 42, rare_events=False)
        for name in ("cells", "red_cells", "debris", "hyphae", "nutrients"):
            getattr(world, name).clear()
        world.bacteria.clear()
        world.phages.clear()
        if kind == "cell":
            obj = Cell(0, 40, 40, 13, 0, 0)
            world.cells = [obj]
            world.lab.lyse(world, Target("cell", obj), 53, 40)
        elif kind == "red":
            obj = Drifter(40, 40, 0, 5)
            world.red_cells = [obj]
            world.lab.lyse(world, Target("red", obj), 44, 40)
        else:
            world.bacteria = {
                i: Bacterium(i, 46 + i * 3, 35 + i * 3, 2, 1, "rod", 999, 999) for i in range(3)
            }
            world.lab.feed(world, 40, 40)
            world.lab.stir(world, 43, 40)
        for _ in range(round(at / STEP)):
            world.update(events=False)
        frame = render(world, True)
        crop = Frame(48, 26)
        for y in range(crop.height):
            for x in range(crop.width):
                crop.pixels[y][x] = frame.pixels[y + 7][x + 16]
        panels.append((label, crop))
    atlas(
        Path(__file__).resolve().parents[1] / "docs/experiments.svg",
        "Interactive microscope / experimental effects use simulated time",
        panels,
    )


if __name__ == "__main__":
    main()
