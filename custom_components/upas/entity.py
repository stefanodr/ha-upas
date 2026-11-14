"""Base comune delle entita'."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN


def device_info(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Un Posto al Sole",
        manufacturer="Community",
        model="Anticipazioni e notizie",
        entry_type=DeviceEntryType.SERVICE,
    )


def air_time_of(options) -> tuple[int, int]:
    """Orario di inizio ("HH:MM") dalle opzioni, con riserva sul default."""
    from .const import CONF_AIR_TIME, DEFAULT_AIR_TIME

    raw = str(options.get(CONF_AIR_TIME) or DEFAULT_AIR_TIME)[:5]
    try:
        hour, minute = (int(x) for x in raw.split(":"))
        if 0 <= hour < 24 and 0 <= minute < 60:
            return hour, minute
    except ValueError:
        pass
    hour, minute = (int(x) for x in DEFAULT_AIR_TIME.split(":"))
    return hour, minute
