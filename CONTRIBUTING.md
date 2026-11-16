# Contributing

Small improvements to animation, organism behavior, accessibility, performance,
and platform support are welcome. This is a biological illustration: shapes and
timings are exaggerated so they remain readable in a terminal.

## Local setup

Use Python 3.10+ with curses on Linux or macOS, or inside WSL. Runtime code uses
only the standard library. Work in an isolated environment for development:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
ruff check .
ruff format --check .
python -m unittest discover -s tests -v
```

Run `./cells --seed 42` to explore interactively, or use a reproducible snapshot:

```sh
cells --snapshot --seed 42 --size 100x32 --at 30
```

## Making changes

- Keep data/geometry in `terminal_cells/models.py`, updates in `world.py`,
  pure drawing in `render.py`, and terminal/argument handling in `cli.py`.
  Drawing must not mutate the world or consume its random number generator.
- Use `world.rng` for simulation randomness. Within a program version, a seed, size, and sequence of
  simulation steps must reproduce the same world.
- Respect membrane boundaries, ownership during capture, and population caps.
- Preserve ASCII, colorless, and small-terminal behavior when changing visuals.
- Add focused regression tests for behavior changes. Use simulated time rather
  than sleeping; pseudo-terminal tests cover terminal interaction and cleanup.

Run the test suite before submitting a pull request. For visible changes,
include a screenshot or short recording and the seed, size, and simulation time.
Regenerate relevant previews with `python tools/preview.py`. To regenerate the
animated demo, run `python tools/demo.py`; Pillow is a development dependency.
The generator uses Noto Sans Runic or FreeMono when available for compact phages;
use `--symbol-font PATH` to supply a Runic-capable font on other systems.

For packaging changes, run the release validation commands in
[the release guide](docs/RELEASING.md). The source archive and installed wheel
must work outside the repository.

## Reporting issues

Include the program version (`cells --version`), operating system, Python
version, terminal application, terminal size, and any relevant flags. A seed
and approximate simulation time make animation problems much easier to reproduce.
Native Windows support is not yet claimed; identify WSL separately from Windows.

Submit a focused pull request describing the problem, resulting behavior, and
validation. Contributions are accepted under the same [Zero-Clause BSD license](LICENSE)
(SPDX: `0BSD`) as the project. By submitting a contribution, you license it under
those terms. No copyright assignment or separate contributor license agreement
is required. Only submit work you have the right to contribute, and identify any
third-party material and its applicable terms.

## Generated tests and performance

Hypothesis explores seeded update/resize sequences, including tiny windows and
scene presets. It checks finite geometry, population bounds, determinism, and
rendering purity. The optional test is skipped when Hypothesis is absent; CI
installs it. Preserve regressions as focused ordinary tests if an example exposes
a bug. `python tools/benchmark.py` reports update/render p50 and p95 latencies;
it excludes terminal output and does not impose hardware-dependent test limits.

Regenerate `docs/cells.1` with `python tools/manpage.py` after changing CLI help.
Run `ruff format .` before submitting formatting changes. `cells.py` and the
`cells` executable remain source-checkout entry points; installed commands use
`terminal_cells.cli:main`. Curses is imported only when interactive mode starts.

Rare-event state and behavior live in `terminal_cells/events.py`; drawings live
in `event_render.py`. Keep event scheduling on the director's seeded RNG and
interactive wall-time clock, independent of simulation speed. Regenerate
`tools/sightings.py` and `tools/colors.py` previews when changing events or inks.

Experimental tools keep model effects in `terminal_cells/lab.py`, input and the
targeting and single-line footer in `interaction.py`, and pure drawing in
`lab_render.py`. Preserve compartment ownership, immediate rupture, bounded
feedback, and mouse restoration
on every exit path. `python tools/experiments.py` regenerates the tool previews.
