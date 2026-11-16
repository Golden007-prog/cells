#!/usr/bin/env python3
"""Build wheels twice in clean source copies and compare their complete bytes."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--epoch", type=int, help="fixed Unix timestamp; otherwise use SOURCE_DATE_EPOCH"
    )
    args = cli.parse_args()
    epoch = str(args.epoch) if args.epoch is not None else os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is None or not epoch.isdecimal():
        cli.error("set SOURCE_DATE_EPOCH to the release commit timestamp, or supply --epoch")
    root = Path(__file__).resolve().parents[1]
    excluded = shutil.ignore_patterns(
        ".git", ".venv", "__pycache__", "*.egg-info", "dist", "build", ".hypothesis", ".ruff_cache"
    )
    env = dict(os.environ, SOURCE_DATE_EPOCH=epoch, PYTHONHASHSEED="0")
    payloads = []
    with tempfile.TemporaryDirectory(prefix="cells-repro-") as directory:
        for name in ("first", "second"):
            copy = Path(directory) / name
            shutil.copytree(root, copy, ignore=excluded)
            subprocess.run(
                [sys.executable, "-m", "build", "--wheel", "--no-isolation"],
                cwd=copy,
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            wheels = list((copy / "dist").glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError("Expected one wheel")
            payloads.append(wheels[0].read_bytes())
    if payloads[0] != payloads[1]:
        print("Wheel builds differ", file=sys.stderr)
        return 1
    print(f"Identical wheel builds: {hashlib.sha256(payloads[0]).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
