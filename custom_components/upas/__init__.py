"""Un Posto al Sole: trame settimanali e notizie in stile quotidiano."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import CARD_FILENAME, DOMAIN, FRONTEND_URL_BASE, PLATFORMS
from .coordinator import UpasCoordinator

_LOGGER = logging.getLogger(__name__)

type UpasConfigEntry = ConfigEntry[UpasCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def _async_ensure_resource(hass: HomeAssistant, url: str) -> None:
    """Aggiunge (o aggiorna) la risorsa della card nelle risorse Lovelace.

    Funziona con le dashboard in modalità storage; in modalità YAML le risorse
    sono statiche e restano a carico dell'utente (resta attivo add_extra_js_url).
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA

        resources = hass.data[LOVELACE_DATA].resources
        if not hasattr(resources, "async_create_item"):
            return  # modalità YAML
        if not resources.loaded:
            await resources.async_load()
            resources.loaded = True
        base = f"{FRONTEND_URL_BASE}/{CARD_FILENAME}"
        mine = [i for i in resources.async_items() if str(i.get("url", "")).split("?")[0] == base]
        if not mine:
            await resources.async_create_item({"res_type": "module", "url": url})
        elif mine[0]["url"] != url:
            await resources.async_update_item(mine[0]["id"], {"res_type": "module", "url": url})
    except Exception as err:  # noqa: BLE001 - non deve mai bloccare l'integrazione
        _LOGGER.debug("Registrazione automatica della risorsa non riuscita: %s", err)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve e registra la card Lovelace inclusa nell'integrazione."""
    card = Path(__file__).parent / "frontend" / CARD_FILENAME
    url = f"{FRONTEND_URL_BASE}/{CARD_FILENAME}"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(url, str(card), cache_headers=False)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    versioned = f"{url}?v={integration.version}"
    add_extra_js_url(hass, versioned)
    await _async_ensure_resource(hass, versioned)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: UpasConfigEntry) -> bool:
    coordinator = UpasCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UpasConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
