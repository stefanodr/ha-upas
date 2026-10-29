"""Contenuti editoriali statici: pillole "Lo sapevi che?" e personaggi del giorno, ciascuno con la fonte."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
TRIVIA_FILE = DATA_DIR / "trivia.json"
CHARACTERS_FILE = DATA_DIR / "characters.json"


def _load(path: Path, key: str) -> list[dict[str, Any]]:
    """Legge un elenco JSON tenendo solo le voci con il campo richiesto e un link alla fonte."""
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [i for i in items if i.get(key) and i.get("url")]


def load_trivia(path: Path = TRIVIA_FILE) -> list[dict[str, Any]]:
    """Legge le pillole (bloccante: chiamare in executor)."""
    return _load(path, "text")


def load_characters(path: Path = CHARACTERS_FILE) -> list[dict[str, Any]]:
    """Legge le schede dei personaggi (bloccante: chiamare in executor)."""
    return [i for i in _load(path, "caption") if i.get("name") and i.get("actor")]


def _day_number(today: date) -> int:
    return (today - date(1970, 1, 1)).days


def pick_trivia(items: list[dict[str, Any]], today: date, skip: int = 0) -> dict[str, Any] | None:
    """Pillola del giorno: quella legata alla ricorrenza (campo "on" = MM-DD) oppure a rotazione.

    La stessa formula è usata dalla card (JavaScript), così sensore e card concordano.
    """
    if not items:
        return None
    mmdd = f"{today.month:02d}-{today.day:02d}"
    anniversary = next((i for i, t in enumerate(items) if t.get("on") == mmdd), None)
    base = anniversary if anniversary is not None else _day_number(today) % len(items)
    return items[(base + skip) % len(items)]


def pick_character(
    items: list[dict[str, Any]], today_text: str, today: date, skip: int = 0
) -> tuple[dict[str, Any], bool] | None:
    """Personaggio del giorno: preferisce chi è citato nella trama di oggi, altrimenti rotazione.

    Restituisce (personaggio, citato_nella_trama). Stessa logica della card.
    """
    if not items:
        return None

    def cited(c: dict[str, Any]) -> bool:
        aliases = c.get("aliases") or [c["name"].split(" ")[0]]
        return any(
            re.search(rf"(^|[^A-Za-zà-ÿ]){re.escape(a)}([^A-Za-zà-ÿ]|$)", today_text or "")
            for a in aliases
        )

    in_plot = [i for i, c in enumerate(items) if cited(c)]
    pool = in_plot or list(range(len(items)))
    idx = pool[(_day_number(today) + skip) % len(pool)]
    return items[idx], idx in in_plot
