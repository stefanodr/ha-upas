"""Test delle funzioni della 1.0: pause, filtri, archivio, calendario, evento, servizio, Repairs."""
from datetime import date

from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.upas.const import DOMAIN, ISSUE_SOURCES, NEWS_URL, NEWS_URL_BING, PLOTS_TAG_URL
from custom_components.upas.parsers import detect_pause, filter_news, parse_week_article, split_words

from .test_integration import FIX, NEXT_URL, WEEK_URL, _entry, _mock


def test_detect_pause():
    assert detect_pause("Oggi la puntata non va in onda per un evento sportivo.")
    assert detect_pause("Puntata sospesa per la maratona elettorale")
    assert not detect_pause("Eduardo prende una pausa dal lavoro e riflette.")


def test_parse_week_marks_paused_day():
    html = (FIX / "week_19_23_ott.html").read_text()
    html = html.replace("Eduardo", "La puntata non va in onda oggi. Eduardo", 1)
    week = parse_week_article(html, date(2026, 10, 19), "u", "s")
    assert any(d["no_episode"] and d["pause_note"] for d in week["days"])
    assert any(not d["no_episode"] for d in week["days"])


def test_filter_news_and_split_words():
    items = [
        {"title": "Un posto al sole: calcio e gossip", "source": "A"},
        {"title": "Anticipazioni", "source": "Gossip Magazine"},
        {"title": "Trame della settimana", "source": "B"},
    ]
    assert split_words("calcio, Gossip;") == ["calcio", "Gossip"]
    assert [i["source"] for i in filter_news(items, ["gossip"])] == ["B"]
    assert filter_news(items, []) == items


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_service_calendar_archive_and_blocklist(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    entry = _entry({"news_blocklist": "xyz-nessuna"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    res = await hass.services.async_call(DOMAIN, "get_summary", {"scope": "today"}, blocking=True, return_response=True)
    assert res["episode"]["date"] == "2026-10-22" and "Eduardo" in res["episode"]["excerpt"]
    res = await hass.services.async_call(DOMAIN, "get_summary", {"scope": "yesterday"}, blocking=True, return_response=True)
    assert res["episode"]["date"] == "2026-10-21"
    res = await hass.services.async_call(DOMAIN, "get_summary", {"scope": "next_week"}, blocking=True, return_response=True)
    assert res["week"]["available"] is False
    res = await hass.services.async_call(DOMAIN, "get_summary", {"scope": "news"}, blocking=True, return_response=True)
    assert len(res["articles"]) == 4

    cal = hass.states.get("calendar.un_posto_al_sole_episodes")
    assert cal is not None and cal.attributes["message"] == "Un Posto al Sole"
    assert entry.runtime_data.archive()  # settimana salvata nell'archivio

    edition = next(s for s in hass.states.async_all("sensor") if s.attributes.get("upas_role") == "edition")
    assert edition.attributes["masthead_title"] == "Un Posto al Sole"
    assert edition.attributes["yesterday"]["date"] == "2026-10-21"


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_blocklist_removes_news(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    first = (FIX / "news.xml").read_text()
    word = filter_word = None
    from custom_components.upas.parsers import parse_news_rss

    word = parse_news_rss(first, 10)[0]["source"].split()[0]
    entry = _entry({"news_blocklist": word, "news_sources": ["google"]})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert all(word.lower() not in n["source"].lower() for n in entry.runtime_data.data["news"])


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_archive_survives_outage_and_repair_issue(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coord = entry.runtime_data

    aioclient_mock._mocks.clear()
    for url in (PLOTS_TAG_URL, WEEK_URL, NEXT_URL, NEWS_URL, NEWS_URL_BING):
        aioclient_mock.get(url, status=500)
    for _ in range(4):
        await coord.async_refresh()
    assert coord.last_update_success  # dati vecchi mantenuti: le entita' restano disponibili
    assert coord.data["weeks"]["this"]["available"] is True
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_SOURCES) is not None

    aioclient_mock._mocks.clear()
    _mock(aioclient_mock)
    await coord.async_refresh()
    assert coord.last_update_success
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_SOURCES) is None


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_week_published_event(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    events = []
    hass.bus.async_listen("upas_event", lambda e: events.append(e.data))

    aioclient_mock._mocks.clear()
    _mock(aioclient_mock, next_week=True)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert events and events[0]["type"] == "week_published"
    state = hass.states.get("event.un_posto_al_sole_broadcast")
    assert state.attributes["event_type"] == "week_published"


@freeze_time("2026-10-22 20:49:59+02:00")
async def test_episode_starting_event(hass: HomeAssistant, aioclient_mock) -> None:
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    await hass.config.async_set_time_zone("Europe/Rome")
    _mock(aioclient_mock)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    state = hass.states.get("event.un_posto_al_sole_broadcast")
    assert state.attributes["event_type"] == "episode_starting"


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_diagnostics(hass: HomeAssistant, aioclient_mock) -> None:
    from custom_components.upas.diagnostics import async_get_config_entry_diagnostics

    _mock(aioclient_mock)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["weeks"]["this"]["available"] is True and diag["news_count"] == 4
