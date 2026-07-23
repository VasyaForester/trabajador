"""Run the Telegram bot using project .venv when available."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_venv() -> None:
    root = Path(__file__).resolve().parent
    if os.name == "nt":
        venv_python = root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root / ".venv" / "bin" / "python"

    in_venv = getattr(sys, "base_prefix", sys.prefix) != sys.prefix
    if in_venv or not venv_python.exists():
        return
    if Path(sys.executable).resolve() == venv_python.resolve():
        return

    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])


_ensure_venv()

from bot.main import main  # noqa: E402

if __name__ == "__main__":
    main()
