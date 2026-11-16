#!/usr/bin/env python3
"""Illustrate rare sightings with controlled states and the real renderer."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terminal_cells import World, Cell, Bacterium, Frame, render  # noqa: E402
from terminal_cells.events import Sighting, Meal  # noqa: E402
from preview import atlas


def main():
    panels = []
    for kind, age, caption in [
        ("rotifer", 30, "Rotifer / cilia, mastax, and feeding"),
        ("net", 6, "Neutrophil / chromatin unfolding"),
        ("net", 20, "DNA trap / extracellular strands"),
        ("pipette", 12, "Micropipette / nutrient droplet"),
    ]:
        world = World(120, 40, 23)
        world.cells.clear()
        world.bacteria.clear()
        world.red_cells.clear()
        world.debris.clear()
        world.hyphae.clear()
        world.phages.clear()
        world.nutrients.clear()
        event = Sighting(kind, 40, 40, age=age, radius=11, phase="feeding", traveled=36)
        world.events.active = event
        if kind == "rotifer":
            event.meals = [Meal("rod", 1.5)]
            world.bacteria = {
                i: Bacterium(
                    i, 58 + i * 2, 34 + i * 3, 2, 0, ("rod", "coccus", "vibrio")[i], 999, 999
                )
                for i in range(3)
            }
        elif kind == "net":
            if age < 10:
                world.cells = [Cell(0, 40, 40, 11, 0, 0, kind="neutrophil")]
                event.source = 0
            else:
                world.bacteria = {0: Bacterium(0, 49, 40, 0, 0, "rod", 999, 999)}
                event.held = {0}
        else:
            event.dropped = event.deposited = True
            world._add_nutrient(43, 40, 5)
        frame = render(world, True)
        crop = Frame(48, 26)
        for y in range(crop.height):
            for x in range(crop.width):
                crop.pixels[y][x] = frame.pixels[y + 7][x + 16]
        panels.append((caption, crop))
    atlas(
        Path(__file__).resolve().parents[1] / "docs/sightings.svg",
        "Rare sightings / simplified and time-compressed microscopy stories",
        panels,
    )


if __name__ == "__main__":
    main()
