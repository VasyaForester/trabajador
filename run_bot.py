"""Run the Telegram bot. Prefer: .\\.venv\\Scripts\\python.exe run_bot.py"""
from __future__ import annotations

import sys
from pathlib import Path


def _using_project_venv() -> bool:
    root = Path(__file__).resolve().parent
    venv_dir = (root / ".venv").resolve()
    try:
        exe = Path(sys.executable).resolve()
    except OSError:
        return False
    return venv_dir in exe.parents or exe == (venv_dir / "Scripts" / "python.exe")


if not _using_project_venv():
    venv_py = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    print(
        "Запусти через venv, чтобы не было двух процессов:\n"
        f"  {venv_py} run_bot.py\n"
        "или scripts\\start_bot.cmd",
        file=sys.stderr,
    )
    sys.exit(2)

from bot.main import main  # noqa: E402

if __name__ == "__main__":
    main()
