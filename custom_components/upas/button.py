"""Pulsante per forzare l'aggiornamento."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import UpasConfigEntry
from .coordinator import UpasCoordinator
from .entity import device_info

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: UpasConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([UpasRefreshButton(entry.runtime_data, entry)])


class UpasRefreshButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh"

    def __init__(self, coordinator: UpasCoordinator, entry: UpasConfigEntry) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = device_info(entry.entry_id)

    async def async_press(self) -> None:
        await self._coordinator.async_refresh()
