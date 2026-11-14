"""Calendario delle puntate (trame note, passate e future)."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import UpasConfigEntry
from .const import EPISODE_MINUTES
from .coordinator import UpasCoordinator
from .entity import air_time_of, device_info

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: UpasConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([UpasCalendar(entry.runtime_data, entry)])


class UpasCalendar(CoordinatorEntity[UpasCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "episodes"
    _attr_icon = "mdi:television-classic"

    def __init__(self, coordinator: UpasCoordinator, entry: UpasConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = device_info(entry.entry_id)

    def _events(self) -> list[CalendarEvent]:
        hour, minute = air_time_of(self.coordinator.config_entry.options)
        tz = dt_util.get_default_time_zone()
        events: list[CalendarEvent] = []
        for ep in self.coordinator.all_episodes():
            if ep.get("no_episode"):
                continue
            day = datetime.fromisoformat(ep["date"])
            start = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + timedelta(minutes=EPISODE_MINUTES),
                    summary="Un Posto al Sole",
                    description=f"{ep['excerpt']}\n\n{ep['source']}: {ep['url']}",
                    location="Rai 3",
                )
            )
        return events

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        upcoming = [e for e in self._events() if e.end > now]
        return min(upcoming, key=lambda e: e.start) if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [e for e in self._events() if e.end > start_date and e.start < end_date]
