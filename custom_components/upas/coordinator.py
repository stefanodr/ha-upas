"""Coordinator: scarica trame settimanali e notizie."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MAX_NEWS,
    CONF_NEWS_ENABLED,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_NEWS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NEWS_URLS,
    PLOTS_ARTICLE_URL,
    PLOTS_BASE,
    PLOTS_SOURCE_NAME,
    PLOTS_TAG_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from .trivia import load_trivia
from .parsers import (
    empty_week,
    extract_week_links,
    merge_news,
    parse_news_rss,
    parse_week_article,
    reference_monday,
    slug_candidates,
)

_LOGGER = logging.getLogger(__name__)
_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"}


class UpasCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Aggiorna periodicamente l'"edizione" del quotidiano."""

    config_entry: ConfigEntry
    trivia: list[dict[str, Any]]

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )

    async def _async_setup(self) -> None:
        """Carica una volta sola le pillole "Lo sapevi che?"."""
        self.trivia = await self.hass.async_add_executor_job(load_trivia)

    # ------------------------------------------------------------- HTTP
    async def _get(self, url: str) -> str | None:
        """GET tollerante: None se la pagina non esiste o la fonte è ko."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                url,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                return await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Fonte non raggiungibile %s: %s", url, err)
            return None

    # ------------------------------------------------------------ trame
    async def _fetch_week(
        self, monday: date, links: dict[date, str]
    ) -> dict[str, Any] | None:
        candidates: list[str] = []
        if monday in links:
            candidates.append(links[monday])
        candidates += [
            PLOTS_ARTICLE_URL.format(span=s.rsplit("-", 1)[0], year=s.rsplit("-", 1)[1])
            for s in slug_candidates(monday)
        ]
        tried: set[str] = set()
        for url in candidates:
            if url in tried:
                continue
            tried.add(url)
            html = await self._get(url)
            if not html:
                continue
            week = await self.hass.async_add_executor_job(
                parse_week_article, html, monday, url, PLOTS_SOURCE_NAME
            )
            if week:
                return week
        return None

    async def _fetch_plots(self, monday: date) -> dict[str, dict[str, Any]]:
        tag_html = await self._get(PLOTS_TAG_URL)
        links: dict[date, str] = {}
        if tag_html:
            links = await self.hass.async_add_executor_job(
                extract_week_links, tag_html, PLOTS_BASE
            )
        weeks: dict[str, dict[str, Any]] = {}
        for key, start in (("this", monday), ("next", monday + timedelta(days=7))):
            week = await self._fetch_week(start, links)
            if week is None:
                previous = (self.data or {}).get("weeks", {}).get(key)
                if previous and previous.get("start") == start.isoformat():
                    week = previous  # tieni l'ultima versione buona
                else:
                    week = empty_week(start)
            weeks[key] = week
        return weeks

    # ----------------------------------------------------------- notizie
    async def _fetch_news(self) -> list[dict[str, Any]]:
        opts = self.config_entry.options
        if not opts.get(CONF_NEWS_ENABLED, True):
            return []
        limit = int(opts.get(CONF_MAX_NEWS, DEFAULT_MAX_NEWS))
        lists: list[list[dict[str, Any]]] = []
        for url in NEWS_URLS:
            xml_text = await self._get(url)
            if xml_text:
                lists.append(
                    await self.hass.async_add_executor_job(parse_news_rss, xml_text, limit)
                )
        if not lists:  # nessuna fonte raggiungibile: tieni le ultime notizie buone
            return (self.data or {}).get("news", [])
        return merge_news(lists, limit)

    # ------------------------------------------------------------ update
    async def _async_update_data(self) -> dict[str, Any]:
        today = dt_util.now().date()
        monday = reference_monday(today)
        weeks = await self._fetch_plots(monday)
        news = await self._fetch_news()
        if not any(w["available"] for w in weeks.values()) and not news:
            raise UpdateFailed("Nessuna fonte raggiungibile (trame e notizie)")
        return {
            "updated": dt_util.utcnow().isoformat(),
            "weeks": weeks,
            "news": news,
            "trivia": self.trivia,
        }
