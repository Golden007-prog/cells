"""Terminal policy, incremental output, headless compatibility, and UI bounds."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from terminal_cells import Frame, Ink, STEP, World
from terminal_cells.cli import TerminalRenderer, advance_frame, main, parser, use_color, use_unicode
from terminal_cells.render import help_lines


class FakeCurses:
    class error(Exception):
        pass

    COLORS = 256
    COLOR_BLACK, COLOR_WHITE, A_BOLD = 0, 7, 256

    def __init__(self, colors=True, defaults=True):
        self.colors, self.defaults = colors, defaults
        self.pairs = []
        self.updates = 0

    def has_colors(self):
        return self.colors

    def start_color(self):
        pass

    def use_default_colors(self):
        if not self.defaults:
            raise self.error()

    def init_pair(self, *args):
        self.pairs.append(args)

    def color_pair(self, number):
        return number << 9

    def doupdate(self):
        self.updates += 1


class Screen:
    def __init__(self, error=None):
        self.writes = []
        self.erases = 0
        self.error = error

    def erase(self):
        self.erases += 1

    def addstr(self, *args):
        self.writes.append(args)
        if self.error:
            raise self.error()

    def noutrefresh(self):
        pass


class TerminalTests(unittest.TestCase):
    def test_help_hides_inactive_tools_and_separates_interactive_controls(self):
        ambient = help_lines()
        interactive = help_lines(interactive=True)
        self.assertNotIn("Microscope tools", ambient)
        self.assertFalse(any("reticle" in line or "Lyse" in line for line in ambient))
        start = interactive.index("Microscope tools")
        self.assertEqual(interactive[start - 1 : start + 2], ["", "Microscope tools", ""])
        for tool in ("Inspect", "Lyse", "Feed", "Stir"):
            self.assertEqual(sum(tool in line for line in interactive), 1)
        self.assertIn("Tab            select the next entity", interactive)
        self.assertEqual(
            help_lines(), ambient, "building interactive help must not alter ambient help"
        )

    def test_color_policy_and_no_color_convention(self):
        for value, automatic in (("", True), ("1", False)):
            with patch.dict(os.environ, {"NO_COLOR": value}):
                self.assertEqual(use_color("auto"), automatic)
                self.assertTrue(use_color("always"))
                self.assertFalse(use_color("never"))

    def test_basic_colors_and_light_background_fallback(self):
        backend = FakeCurses(defaults=False)
        backend.COLORS = 8
        TerminalRenderer(Screen(), "light", "always", backend)
        self.assertEqual(len(backend.pairs), len(Ink))
        self.assertTrue(
            all(
                0 <= foreground < 8 and background == 7
                for _, foreground, background in backend.pairs
            )
        )
        disabled = FakeCurses(colors=False)
        TerminalRenderer(Screen(), "slide", "always", disabled)
        self.assertFalse(disabled.pairs)

    def test_diff_output_resize_and_bottom_right_errors(self):
        backend, screen = FakeCurses(), Screen()
        renderer = TerminalRenderer(screen, "slide", "never", backend)
        frame = Frame(5, 3)
        renderer.draw(frame)
        screen.writes.clear()
        renderer.draw(frame)
        self.assertFalse(screen.writes)
        changed = Frame(5, 3)
        changed.text(1, 1, "xx", Ink.RED, True)
        renderer.draw(changed)
        self.assertEqual(screen.writes, [(1, 1, "xx", backend.A_BOLD)])
        renderer.draw(Frame(6, 4))
        self.assertEqual(screen.erases, 2)
        screen.error = backend.error
        renderer.draw(Frame(1, 1))  # curses ERR must not lose future redraws
        self.assertEqual(renderer.previous.width, 1)

    def test_unicode_selection_and_alias(self):
        self.assertTrue(use_unicode("auto", "UTF-8"))
        self.assertFalse(use_unicode("auto", "ascii"))
        self.assertFalse(use_unicode("never", "UTF-8"))
        self.assertTrue(use_unicode("always", "ascii"))
        self.assertEqual(parser().parse_args(["--ascii"]).unicode, "never")
        self.assertEqual(parser().parse_args([]).unicode, "auto")

    def test_catchup_bounds_preserve_fixed_steps(self):
        world = World(80, 24, 42)
        remaining = advance_frame(world, 100)
        self.assertAlmostEqual(world.time, STEP * 6)
        self.assertAlmostEqual(remaining, STEP * 6)
        advance_frame(world, STEP / 2)
        self.assertAlmostEqual(world.time, STEP * 6)

    def test_calm_defaults_and_explicit_override(self):
        cli = importlib.import_module("terminal_cells.cli")
        with (
            patch.object(cli.sys.stdin, "isatty", return_value=True),
            patch.object(cli.sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}),
            patch.object(cli, "load_curses") as load,
        ):
            main(["--calm"])
            first = load.return_value.wrapper.call_args.args[1]
            self.assertEqual((first.speed, first.fps), (0.5, 10))
            main(["--calm", "--speed", "2", "--fps", "24"])
            second = load.return_value.wrapper.call_args.args[1]
            self.assertEqual((second.speed, second.fps), (2, 24))

    def test_headless_commands_without_curses(self):
        root = Path(__file__).resolve().parents[1]
        code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname in ('curses', '_curses'):
            raise ImportError('curses intentionally unavailable')
sys.meta_path.insert(0, Block())
from terminal_cells.cli import main
raise SystemExit(main(sys.argv[1:]))
"""
        for args in (["--help"], ["--version"], ["--snapshot", "--at", "0"], ["--diagnostics"]):
            result = subprocess.run(
                [sys.executable, "-c", code, *args], cwd=root, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("\x1b", result.stdout)
        report = json.loads(result.stdout)
        self.assertFalse(report["curses_available"])

    def test_missing_curses_interactive_has_actionable_error(self):
        cli = importlib.import_module("terminal_cells.cli")
        output = io.StringIO()
        with (
            patch.object(cli.sys.stdin, "isatty", return_value=True),
            patch.object(cli.sys.stdout, "isatty", return_value=True),
            patch.dict(os.environ, {"TERM": "xterm"}),
            patch.object(cli, "load_curses", side_effect=ImportError()),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(main([]), 2)
        self.assertIn("--snapshot", output.getvalue())

    def test_scene_composition_and_validation(self):
        microbial = World(100, 32, 42, scene="microbial")
        for _ in range(3300):
            microbial.update()
        self.assertFalse(microbial.cells)
        self.assertFalse(microbial.red_cells)
        blood = World(100, 32, 42, scene="blood")
        for _ in range(1600):
            blood.update()
        self.assertFalse(blood.hyphae)
        self.assertTrue(blood.cells)
        with self.assertRaises(ValueError):
            World(80, 24, 1, scene="unknown")
