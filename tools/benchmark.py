#!/usr/bin/env python3
"""Report update and render latency; measurements exclude terminal output."""

from pathlib import Path
import argparse
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terminal_cells import World, render  # noqa: E402


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--samples", type=int, default=100)
    args = cli.parse_args()
    if args.samples < 2:
        cli.error("--samples must be at least 2")
    for width, height in ((80, 24), (120, 40), (200, 60)):
        world = World(width, height, 42)
        for _ in range(1800):
            world.update()
        results = []
        for operation in (world.update, lambda: render(world)):
            timings = []
            for _ in range(args.samples):
                start = time.perf_counter()
                operation()
                timings.append((time.perf_counter() - start) * 1000)
            results.append(
                f"{statistics.median(timings):.2f}/{sorted(timings)[int(0.95 * (len(timings) - 1))]:.2f} ms"
            )
        print(f"{width}x{height}: update p50/p95 {results[0]}; render p50/p95 {results[1]}")


if __name__ == "__main__":
    main()
