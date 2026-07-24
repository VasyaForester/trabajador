"""Run the Telegram bot using the project virtualenv (Windows or Linux)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _venv_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def _using_project_venv() -> bool:
    venv_dir = (ROOT / ".venv").resolve()
    if not venv_dir.exists():
        return False
    try:
        exe = Path(sys.executable).resolve()
    except OSError:
        return False
    if venv_dir in exe.parents:
        return True
    candidates = {
        (venv_dir / "Scripts" / "python.exe").resolve(),
        (venv_dir / "bin" / "python").resolve(),
        (venv_dir / "bin" / "python3").resolve(),
    }
    # resolve() may fail if file missing
    existing = set()
    for c in candidates:
        try:
            if c.exists():
                existing.add(c.resolve())
        except OSError:
            pass
    return exe in existing


if not _using_project_venv():
    venv_py = _venv_python()
    if venv_py.exists():
        # Re-launch with project venv (needed on Linux if started with system python)
        os.execv(str(venv_py), [str(venv_py), str(Path(__file__).resolve()), *sys.argv[1:]])
    print(
        "Не найден project venv. Создайте его и установите зависимости:\n"
        f"  python3 -m venv {ROOT / '.venv'}\n"
        f"  {ROOT / '.venv' / 'bin' / 'pip'} install -r requirements.txt\n"
        f"Затем: {venv_py} run_bot.py",
        file=sys.stderr,
    )
    sys.exit(2)

from bot.main import main  # noqa: E402

if __name__ == "__main__":
    main()
