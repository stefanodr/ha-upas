"""Diagnostica scaricabile (nessun dato personale)."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import UpasConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: UpasConfigEntry) -> dict[str, Any]:
    coord = entry.runtime_data
    data = coord.data or {}
    weeks = data.get("weeks", {})
    return {
        "options": dict(entry.options),
        "last_update_success": coord.last_update_success,
        "consecutive_failures": coord._failures,
        "updated": data.get("updated"),
        "weeks": {
            k: {"start": w.get("start"), "available": w.get("available"), "days": len(w.get("days", [])), "url": w.get("url")}
            for k, w in weeks.items()
        },
        "news_count": len(data.get("news", [])),
        "archive_weeks": sorted(coord.archive()),
    }
