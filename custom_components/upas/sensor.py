"""Sensori Un Posto al Sole."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import UpasConfigEntry
from .const import DOMAIN
from .coordinator import UpasCoordinator
from .trivia import pick_trivia

PARALLEL_UPDATES = 0

DESCRIPTIONS = (
    SensorEntityDescription(
        key="edition",
        translation_key="edition",
        icon="mdi:newspaper-variant-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(key="today", translation_key="today", icon="mdi:television-classic"),
    SensorEntityDescription(key="this_week", translation_key="this_week", icon="mdi:calendar-week"),
    SensorEntityDescription(key="next_week", translation_key="next_week", icon="mdi:calendar-arrow-right"),
    SensorEntityDescription(key="trivia", translation_key="trivia", icon="mdi:lightbulb-on-outline"),
    SensorEntityDescription(key="news", translation_key="news", icon="mdi:newspaper-variant-multiple"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: UpasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(UpasSensor(coordinator, entry, d) for d in DESCRIPTIONS)


class UpasSensor(CoordinatorEntity[UpasCoordinator], SensorEntity):
    """Sensore dell'edizione: i dati completi sono negli attributi."""

    _attr_has_entity_name = True
    # Attributi voluminosi: non servono nello storico del recorder.
    _unrecorded_attributes = frozenset({"days", "articles", "this_week", "next_week", "news", "today", "trivia"})

    def __init__(
        self, coordinator: UpasCoordinator, entry: UpasConfigEntry, description: SensorEntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Un Posto al Sole",
            manufacturer="Community",
            model="Anticipazioni e notizie",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.entity_description.key in ("today", "trivia"):
            # La puntata "di oggi" cambia a mezzanotte, non al prossimo refresh.
            self.async_on_remove(
                async_track_time_change(self.hass, self._midnight, hour=0, minute=1, second=0)
            )

    @callback
    def _midnight(self, _now: datetime) -> None:
        self.async_write_ha_state()

    # ---------------------------------------------------------------- helpers
    def _weeks(self) -> dict[str, Any]:
        return self.coordinator.data.get("weeks", {})

    def _today(self) -> dict[str, Any] | None:
        iso = dt_util.now().date().isoformat()
        for week in self._weeks().values():
            for day in week.get("days", []):
                if day["date"] == iso:
                    return {**day, "url": week["url"], "source": week["source"]}
        return None

    # ------------------------------------------------------------------ stato
    @property
    def native_value(self) -> Any:
        key = self.entity_description.key
        data = self.coordinator.data
        if key == "edition":
            return dt_util.parse_datetime(data["updated"])
        if key == "news":
            return len(data.get("news", []))
        if key == "trivia":
            pill = pick_trivia(data.get("trivia", []), dt_util.now().date())
            return pill["text"][:255] if pill else None
        if key == "today":
            day = self._today()
            return day["excerpt"][:255] if day else "Nessuna puntata oggi"
        week = self._weeks().get(key.removesuffix("_week"))
        if not week:
            return None
        return week["label"] if week["available"] else "In arrivo"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        key = self.entity_description.key
        data = self.coordinator.data
        if key == "edition":
            return {
                "upas_role": "edition",  # la card trova da sola questa entità
                "today": self._today(),
                "this_week": self._weeks().get("this"),
                "next_week": self._weeks().get("next"),
                "news": data.get("news", []),
                "trivia": data.get("trivia", []),
            }
        if key == "trivia":
            pill = pick_trivia(data.get("trivia", []), dt_util.now().date())
            return dict(pill) if pill else {}
        if key == "news":
            return {"articles": data.get("news", [])}
        if key == "today":
            return self._today() or {}
        week = self._weeks().get(key.removesuffix("_week"))
        return dict(week) if week else {}
