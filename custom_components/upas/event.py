"""Entita' evento: nuova settimana pubblicata e puntata in partenza."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.event import EventEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from . import UpasConfigEntry
from .const import BUS_EVENT, EVENT_EPISODE_STARTING, EVENT_WEEK_PUBLISHED
from .coordinator import UpasCoordinator
from .entity import air_time_of, device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: UpasConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([UpasEvent(entry.runtime_data, entry)])


class UpasEvent(EventEntity):
    """Scatta con `week_published` (nuova trama online) e `episode_starting` (all'orario di messa in onda)."""

    _attr_has_entity_name = True
    _attr_translation_key = "broadcast"
    _attr_event_types = [EVENT_WEEK_PUBLISHED, EVENT_EPISODE_STARTING]

    def __init__(self, coordinator: UpasCoordinator, entry: UpasConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_event"
        self._attr_device_info = device_info(entry.entry_id)

    async def async_added_to_hass(self) -> None:
        hour, minute = air_time_of(self._coordinator.config_entry.options)
        self.async_on_remove(
            async_track_time_change(self.hass, self._air, hour=hour, minute=minute, second=0)
        )
        self.async_on_remove(self.hass.bus.async_listen(BUS_EVENT, self._bus))

    @callback
    def _bus(self, event: Event) -> None:
        data = dict(event.data)
        if data.pop("type", None) == EVENT_WEEK_PUBLISHED:
            self._trigger_event(EVENT_WEEK_PUBLISHED, data)
            self.async_write_ha_state()

    @callback
    def _air(self, now: datetime) -> None:
        ep = self._coordinator.episode_for(dt_util.now().date())
        if not ep or ep.get("no_episode"):
            return
        self._trigger_event(EVENT_EPISODE_STARTING, {"date": ep["date"], "excerpt": ep["excerpt"], "url": ep["url"]})
        self.async_write_ha_state()
