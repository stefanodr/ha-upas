"""Pillole "Lo sapevi che?": fatti sulla storia della serie, ciascuno con la fonte."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

TRIVIA_FILE = Path(__file__).parent / "data" / "trivia.json"


def load_trivia(path: Path = TRIVIA_FILE) -> list[dict[str, Any]]:
    """Legge le pillole (bloccante: chiamare in executor)."""
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [i for i in items if i.get("text") and i.get("url")]


def pick_trivia(items: list[dict[str, Any]], today: date, skip: int = 0) -> dict[str, Any] | None:
    """Pillola del giorno: quella legata alla ricorrenza (campo "on" = MM-DD) oppure a rotazione.

    La stessa formula è usata dalla card (JavaScript), così sensore e card concordano.
    """
    if not items:
        return None
    mmdd = f"{today.month:02d}-{today.day:02d}"
    anniversary = next((i for i, t in enumerate(items) if t.get("on") == mmdd), None)
    base = anniversary if anniversary is not None else (today - date(1970, 1, 1)).days % len(items)
    return items[(base + skip) % len(items)]
