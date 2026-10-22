"""Test di integrazione con rete simulata."""
from pathlib import Path

from freezegun import freeze_time
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.upas.const import DOMAIN, NEWS_URL, NEWS_URL_BING, PLOTS_TAG_URL

FIX = Path(__file__).parent / "fixtures"
WEEK_URL = "https://www.sorrisi.com/tv/soap/un-posto-al-sole-le-trame-dal-19-al-23-ottobre-2026/"
NEXT_URL = "https://www.sorrisi.com/tv/soap/un-posto-al-sole-le-trame-dal-26-al-30-ottobre-2026/"
NOV_URL = "https://www.sorrisi.com/tv/soap/un-posto-al-sole-le-trame-dal-2-al-6-novembre-2026/"


def _mock(aioclient_mock: AiohttpClientMocker, next_week: bool = False) -> None:
    aioclient_mock.get(PLOTS_TAG_URL, text=(FIX / "tag_page.html").read_text())
    aioclient_mock.get(WEEK_URL, text=(FIX / "week_19_23_ott.html").read_text())
    if next_week:
        html = (FIX / "week_19_23_ott.html").read_text()
        for a, b in (("19", "26"), ("20", "27"), ("21", "28"), ("22", "29"), ("23", "30")):
            html = html.replace(f"{a} ottobre", f"{b} ottobre")
        aioclient_mock.get(NEXT_URL, text=html)
    else:
        aioclient_mock.get(NEXT_URL, status=404)
    aioclient_mock.get(NOV_URL, status=404)
    aioclient_mock.get(NEWS_URL, text=(FIX / "news.xml").read_text())
    aioclient_mock.get(NEWS_URL_BING, text=(FIX / "news_bing.xml").read_text())


def _entry(options=None) -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, title="Un Posto al Sole", data={}, options=options or {})


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_setup_and_sensors(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    reg = er.async_get(hass)
    ids = {e.unique_id.split("_", 1)[1]: e.entity_id for e in er.async_entries_for_config_entry(reg, entry.entry_id)}
    assert set(ids) == {"edition", "today", "this_week", "next_week", "news"}

    this_week = hass.states.get(ids["this_week"])
    assert this_week.state == "19–23 ottobre"
    assert len(this_week.attributes["days"]) == 5
    assert hass.states.get(ids["next_week"]).state == "In arrivo"  # non ancora pubblicata
    assert hass.states.get(ids["news"]).state == "4"

    today = hass.states.get(ids["today"])
    assert today.attributes["date"] == "2026-10-22"
    assert "Eduardo" in today.state

    edition = hass.states.get(ids["edition"])
    assert edition.attributes["upas_role"] == "edition"
    assert edition.attributes["this_week"]["available"] is True
    assert edition.attributes["next_week"]["available"] is False
    assert len(edition.attributes["news"]) == 4


@freeze_time("2026-10-24 12:00:00+02:00")  # sabato: "corrente" = settimana che inizia lunedì 26
async def test_weekend_shifts_weeks(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock, next_week=True)
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    states = {s.entity_id: s for s in hass.states.async_all("sensor")}
    this_week = next(s for s in states.values() if s.attributes.get("start") == "2026-10-26")
    assert this_week.state == "26–30 ottobre"


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_sources_down_fails_setup(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(PLOTS_TAG_URL, status=500)
    aioclient_mock.get(WEEK_URL, status=500)
    aioclient_mock.get(NEXT_URL, status=500)
    aioclient_mock.get(NEWS_URL, status=500)
    aioclient_mock.get(NEWS_URL_BING, status=500)
    entry = _entry()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


@freeze_time("2026-10-22 12:00:00+02:00")
async def test_news_disabled_and_options_flow(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    entry = _entry({"news_enabled": False, "scan_interval": 120, "max_news": 5})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.data["news"] == []

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"scan_interval": 180, "news_enabled": True, "max_news": 4}
    )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert entry.options["scan_interval"] == 180
    assert entry.runtime_data.data["news"]  # ricaricata con le notizie attive


async def test_config_flow_single_instance(hass: HomeAssistant, aioclient_mock) -> None:
    _mock(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"scan_interval": 360, "news_enabled": True, "max_news": 10}
    )
    assert result["type"] == "create_entry"
    assert result["options"]["scan_interval"] == 360
    await hass.async_block_till_done()
    again = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert again["type"] == "abort"
