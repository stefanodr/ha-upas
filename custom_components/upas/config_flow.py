"""Config flow per Un Posto al Sole."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TimeSelector,
)

from .const import (
    CONF_AIR_TIME,
    CONF_MASTHEAD_TITLE,
    CONF_MAX_NEWS,
    CONF_NEWS_BLOCKLIST,
    CONF_NEWS_ENABLED,
    CONF_NEWS_SOURCES,
    DEFAULT_AIR_TIME,
    DEFAULT_MASTHEAD_TITLE,
    NEWS_FEEDS,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_NEWS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL,
                    max=MAX_SCAN_INTERVAL,
                    step=30,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_NEWS_ENABLED, default=defaults.get(CONF_NEWS_ENABLED, True)
            ): BooleanSelector(),
            vol.Required(
                CONF_MAX_NEWS, default=defaults.get(CONF_MAX_NEWS, DEFAULT_MAX_NEWS)
            ): NumberSelector(
                NumberSelectorConfig(min=3, max=30, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_NEWS_SOURCES, default=defaults.get(CONF_NEWS_SOURCES, list(NEWS_FEEDS))
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[{"value": k, "label": k.capitalize()} for k in NEWS_FEEDS],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
            vol.Optional(
                CONF_NEWS_BLOCKLIST, default=defaults.get(CONF_NEWS_BLOCKLIST, "")
            ): TextSelector(),
            vol.Required(
                CONF_MASTHEAD_TITLE, default=defaults.get(CONF_MASTHEAD_TITLE, DEFAULT_MASTHEAD_TITLE)
            ): TextSelector(),
            vol.Required(
                CONF_AIR_TIME, default=defaults.get(CONF_AIR_TIME, DEFAULT_AIR_TIME)
            ): TimeSelector(),
        }
    )


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
        CONF_NEWS_ENABLED: bool(user_input[CONF_NEWS_ENABLED]),
        CONF_MAX_NEWS: int(user_input[CONF_MAX_NEWS]),
        CONF_NEWS_SOURCES: list(user_input.get(CONF_NEWS_SOURCES) or NEWS_FEEDS),
        CONF_NEWS_BLOCKLIST: str(user_input.get(CONF_NEWS_BLOCKLIST) or "").strip(),
        CONF_MASTHEAD_TITLE: str(user_input.get(CONF_MASTHEAD_TITLE) or DEFAULT_MASTHEAD_TITLE).strip(),
        CONF_AIR_TIME: str(user_input.get(CONF_AIR_TIME) or DEFAULT_AIR_TIME)[:5],
    }


class UpasConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configurazione iniziale (una sola istanza)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Un Posto al Sole", data={}, options=_clean(user_input)
            )
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> "UpasOptionsFlow":
        return UpasOptionsFlow()


class UpasOptionsFlow(OptionsFlowWithReload):
    """Opzioni: ricarica automaticamente l'integrazione al salvataggio."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                _schema(dict(self.config_entry.options)), self.config_entry.options
            ),
        )
