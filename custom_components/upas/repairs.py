"""Riparazioni: riprova subito ad aggiornare le fonti."""
from __future__ import annotations

from homeassistant.components.repairs import ConfirmRepairFlow, RepairsFlow
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class RefreshRepairFlow(ConfirmRepairFlow):
    async def async_step_confirm(self, user_input=None):
        if user_input is not None:
            for entry in self.hass.config_entries.async_loaded_entries(DOMAIN):
                await entry.runtime_data.async_refresh()
        return await super().async_step_confirm(user_input)


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data) -> RepairsFlow:
    return RefreshRepairFlow()
