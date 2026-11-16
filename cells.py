#!/usr/bin/env python3
"""Compatibility entry point; implementation lives in terminal_cells."""

from terminal_cells import *  # noqa: F403
from terminal_cells import __version__, main  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
