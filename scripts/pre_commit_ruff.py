"""Run ruff the same way as CI Test (poetry run, else project .venv, else current Python)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["roboto_guilliman", "tests"]


def _venv_python() -> Path | None:
    for candidate in (
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return candidate
    return None


def _attempt(command: list[str]) -> int | None:
    try:
        completed = subprocess.run(command, cwd=ROOT, check=False)
    except FileNotFoundError:
        return None
    return completed.returncode


def main() -> int:
    commands = [
        ["poetry", "run", "ruff", "check", *TARGETS],
    ]
    venv_python = _venv_python()
    if venv_python is not None:
        commands.append([str(venv_python), "-m", "ruff", "check", *TARGETS])
    commands.append([sys.executable, "-m", "ruff", "check", *TARGETS])

    for command in commands:
        exit_code = _attempt(command)
        if exit_code is not None:
            return exit_code

    print("ruff not found: run poetry install", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
