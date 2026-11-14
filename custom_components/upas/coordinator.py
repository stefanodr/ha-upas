"""Coordinator: scarica trame settimanali e notizie."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ARCHIVE_WEEKS,
    BUS_EVENT,
    CONF_MAX_NEWS,
    CONF_NEWS_BLOCKLIST,
    CONF_NEWS_ENABLED,
    CONF_NEWS_SOURCES,
    EVENT_WEEK_PUBLISHED,
    ISSUE_FAILURES,
    ISSUE_SOURCES,
    NEWS_FEEDS,
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_SCAN_INTERVAL,
    DEFAULT_MAX_NEWS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLOTS_ARTICLE_URL,
    PLOTS_BASE,
    PLOTS_SOURCE_NAME,
    PLOTS_TAG_URL,
    REQUEST_TIMEOUT,
    USER_AGENT,
)
from .trivia import load_characters, load_trivia
from .parsers import (
    empty_week,
    extract_week_links,
    filter_news,
    merge_news,
    parse_news_rss,
    parse_week_article,
    reference_monday,
    slug_candidates,
    split_words,
)

_LOGGER = logging.getLogger(__name__)
_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "it-IT,it;q=0.9"}


class UpasCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Aggiorna periodicamente l'"edizione" del quotidiano."""

    config_entry: ConfigEntry
    trivia: list[dict[str, Any]]
    characters: list[dict[str, Any]]

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
        )
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}")
        self._archive: dict[str, dict[str, Any]] = {}
        self._failures = 0
        self._fresh_plots = False
        self._fresh_news = False

    async def _async_setup(self) -> None:
        """Carica pillole, personaggi e archivio delle settimane gia' viste."""
        stored = await self._store.async_load() or {}
        self._archive = stored.get("weeks", {})
        self.trivia = await self.hass.async_add_executor_job(load_trivia)
        self.characters = await self.hass.async_add_executor_job(load_characters)

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
        self._fresh_plots = bool(tag_html)
        for key, start in (("this", monday), ("next", monday + timedelta(days=7))):
            week = await self._fetch_week(start, links)
            if week is not None:
                self._fresh_plots = True
            if week is None:
                previous = (self.data or {}).get("weeks", {}).get(key)
                if previous and previous.get("start") == start.isoformat() and previous.get("available"):
                    week = previous  # tieni l'ultima versione buona
                else:
                    week = self._archive.get(start.isoformat()) or empty_week(start)
            weeks[key] = week
        prev_start = (monday - timedelta(days=7)).isoformat()
        weeks["previous"] = self._archive.get(prev_start) or empty_week(monday - timedelta(days=7))
        return weeks

    def _remember(self, weeks: dict[str, dict[str, Any]]) -> bool:
        """Salva nell'archivio le settimane disponibili; True se qualcosa e' cambiato."""
        changed = False
        for week in weeks.values():
            if week.get("available") and self._archive.get(week["start"]) != week:
                self._archive[week["start"]] = week
                changed = True
        for start in sorted(self._archive)[:-ARCHIVE_WEEKS]:
            del self._archive[start]
            changed = True
        if changed:
            self._store.async_delay_save(lambda: {"weeks": self._archive}, 5)
        return changed

    def archive(self) -> dict[str, dict[str, Any]]:
        return self._archive

    # ----------------------------------------------------------- notizie
    async def _fetch_news(self) -> list[dict[str, Any]]:
        opts = self.config_entry.options
        self._fresh_news = False
        if not opts.get(CONF_NEWS_ENABLED, True):
            return []
        limit = int(opts.get(CONF_MAX_NEWS, DEFAULT_MAX_NEWS))
        wanted = opts.get(CONF_NEWS_SOURCES) or list(NEWS_FEEDS)
        blocklist = split_words(opts.get(CONF_NEWS_BLOCKLIST))
        lists: list[list[dict[str, Any]]] = []
        for name, url in NEWS_FEEDS.items():
            if name not in wanted:
                continue
            xml_text = await self._get(url)
            if xml_text:
                lists.append(
                    await self.hass.async_add_executor_job(parse_news_rss, xml_text, limit)
                )
        self._fresh_news = bool(lists)
        if not lists:  # nessuna fonte raggiungibile: tieni le ultime notizie buone
            return (self.data or {}).get("news", [])
        return filter_news(merge_news(lists, limit * 2), blocklist)[:limit]

    # ------------------------------------------------------------ update
    async def _async_update_data(self) -> dict[str, Any]:
        today = dt_util.now().date()
        monday = reference_monday(today)
        weeks = await self._fetch_plots(monday)
        news = await self._fetch_news()
        news_on = bool(self.config_entry.options.get(CONF_NEWS_ENABLED, True))
        reached = self._fresh_plots or (news_on and self._fresh_news)
        if not reached:
            self._failures += 1
            if self._failures >= ISSUE_FAILURES:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    ISSUE_SOURCES,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=ISSUE_SOURCES,
                )
            has_data = any(w["available"] for k, w in weeks.items() if k != "previous") or news
            if not has_data or self._failures >= ISSUE_FAILURES * 3:
                raise UpdateFailed("Nessuna fonte raggiungibile (trame e notizie)")
        else:
            self._failures = 0
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_SOURCES)
        was_published = bool((self.data or {}).get("weeks", {}).get("next", {}).get("available"))
        self._remember(weeks)
        if self.data and not was_published and weeks["next"]["available"]:
            self.hass.bus.async_fire(
                BUS_EVENT,
                {"type": EVENT_WEEK_PUBLISHED, "label": weeks["next"]["label"], "url": weeks["next"]["url"]},
            )
        return {
            "updated": dt_util.utcnow().isoformat(),
            "weeks": weeks,
            "news": news,
            "trivia": self.trivia,
            "characters": self.characters,
        }

    # ------------------------------------------------------------ helpers
    def episode_for(self, day: date) -> dict[str, Any] | None:
        """Trama di un giorno (anche passato, dall'archivio) o None."""
        iso = day.isoformat()
        sources = list((self.data or {}).get("weeks", {}).values()) + list(self._archive.values())
        for week in sources:
            for item in week.get("days", []):
                if item["date"] == iso:
                    return {**item, "url": week["url"], "source": week["source"]}
        return None

    def all_episodes(self) -> list[dict[str, Any]]:
        """Tutte le puntate note (archivio + dati correnti), ordinate per data."""
        found: dict[str, dict[str, Any]] = {}
        sources = list(self._archive.values()) + list((self.data or {}).get("weeks", {}).values())
        for week in sources:
            for item in week.get("days", []):
                found[item["date"]] = {**item, "url": week["url"], "source": week["source"]}
        return [found[k] for k in sorted(found)]
