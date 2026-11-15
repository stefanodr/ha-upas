"""Test delle funzioni della 1.0: pause, filtri, archivio, calendario, evento, servizio, Repairs."""
from datetime import date

from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.upas.const import ALT_DISCOVERY_URL, DOMAIN, ISSUE_SOURCES, NEWS_URL, NEWS_URL_BING, PLOTS_TAG_URL
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
    for url in (PLOTS_TAG_URL, WEEK_URL, NEXT_URL, NEWS_URL, NEWS_URL_BING, ALT_DISCOVERY_URL):
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


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_second_source_fills_missing_week(hass: HomeAssistant, aioclient_mock) -> None:
    alt = (FIX / "alt_discovery.xml").read_text()
    _mock(aioclient_mock, alt_discovery=alt)
    aioclient_mock.get(
        "https://dilei.it/spettacolo/un-posto-al-sole-anticipazioni-trame-settimana-26-ottobre-30-ottobre-2026/2600001/",
        text=(FIX / "alt_week_26_30_ott.html").read_text(),
    )
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    nxt = entry.runtime_data.data["weeks"]["next"]
    assert nxt["available"] and nxt["source"] == "DiLei"
    assert [d["date"] for d in nxt["days"]] == [f"2026-10-{n}" for n in (26, 27, 28, 29, 30)]
    assert "Gianluca" in nxt["days"][0]["excerpt"]          # titoletto separato dal testo
    assert "Rossella" in nxt["days"][1]["excerpt"]          # titoletto nello stesso paragrafo
    assert nxt["days"][2]["no_episode"] is True
    assert "Vacanze" not in nxt["days"][4]["excerpt"]       # il riepilogo finale non entra


def test_extract_alt_links():
    from custom_components.upas.const import ALT_ARTICLE_MARK
    from custom_components.upas.parsers import extract_alt_links

    links = extract_alt_links((FIX / "alt_discovery.xml").read_text(), ALT_ARTICLE_MARK)
    assert list(links) == [date(2026, 10, 26)]


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_previous_week_backfilled_once(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    html = (FIX / "week_19_23_ott.html").read_text()
    for a, b in (("19", "12"), ("20", "13"), ("21", "14"), ("22", "15"), ("23", "16")):
        html = html.replace(f"{a} ottobre", f"{b} ottobre")
    aioclient_mock.get("https://www.sorrisi.com/tv/soap/un-posto-al-sole-le-trame-dal-12-al-16-ottobre-2026/", text=html)
    aioclient_mock._mocks.insert(0, aioclient_mock._mocks.pop())  # specifico prima del 404 generico
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    prev = entry.runtime_data.data["weeks"]["previous"]
    assert prev["available"] and prev["start"] == "2026-10-12"


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_button_streak_and_next_break(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    html = (FIX / "week_19_23_ott.html").read_text().replace("venerdì 23 ottobre", "venerdì 23 ottobre")
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coord = entry.runtime_data
    # oggi (gio 22) + ven 23 senza pause note: serie = 2, nessuna pausa
    info = coord.pause_info(date(2026, 10, 22))
    assert info["streak"] == 2 and info["next_pause"] is None
    # una pausa venerdi' -> serie 1 e prossima pausa il 23
    coord.data["weeks"]["this"]["days"][-1]["no_episode"] = True
    coord.data["weeks"]["this"]["days"][-1]["pause_note"] = "Non va in onda"
    info = coord.pause_info(date(2026, 10, 22))
    assert info["streak"] == 1 and info["next_pause"]["date"] == "2026-10-23"
    calls = len(aioclient_mock.mock_calls)
    await hass.services.async_call("button", "press", {"entity_id": "button.un_posto_al_sole_refresh_now"}, blocking=True)
    assert len(aioclient_mock.mock_calls) > calls
    assert hass.states.get("sensor.un_posto_al_sole_next_break") is not None


async def test_repair_flow_refreshes(hass: HomeAssistant, aioclient_mock) -> None:
    from custom_components.upas.repairs import async_create_fix_flow

    flow = await async_create_fix_flow(hass, ISSUE_SOURCES, None)
    assert flow is not None
