"""Parser puri (senza dipendenze da Home Assistant) per trame e notizie.

Tenerli separati dal coordinator permette di testarli con semplici fixture
HTML/XML e di adattarli rapidamente se le fonti cambiano struttura.
"""
from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .const import EPISODE_DAYS, EXCERPT_CHARS

MONTHS = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
    "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10,
    "novembre": 11, "dicembre": 12,
}
MONTH_NAMES = {v: k for k, v in MONTHS.items()}
WEEKDAYS = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]

_WEEKDAY_KEYS = ("lunedi", "martedi", "mercoledi", "giovedi", "venerdi")
_DAY_HEADING = re.compile(
    r"^\s*(lunedi|martedi|mercoledi|giovedi|venerdi)\s+(\d{1,2})\s+([a-z]+)", re.I
)
# "dal 19 al 23 ottobre 2026", "dal 31 agosto al 4 settembre 2026",
# "dal 7 all'11 settembre 2026" e la variante da URL "dal 7 all11 settembre 2026".
_WEEK_SPAN = re.compile(
    r"dal\s+(\d{1,2})(?:\s+([a-z]+))?\s+al(?:l['’]?)?\s*(\d{1,2})\s+([a-z]+)\s+(\d{4})",
    re.I,
)


def _fold(text: str) -> str:
    """Minuscolo senza accenti, spazi normalizzati."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.lower().split())


def clean(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


# ----------------------------------------------------------------- settimane
def reference_monday(today: date) -> date:
    """Lunedì della "settimana corrente".

    Nel weekend non vanno in onda puntate: la settimana "corrente" diventa
    quella che inizia lunedì, così il fine settimana si vede già cosa arriva.
    """
    monday = today - timedelta(days=today.weekday())
    return monday + timedelta(days=7) if today.weekday() >= EPISODE_DAYS else monday


def week_label(monday: date) -> str:
    friday = monday + timedelta(days=EPISODE_DAYS - 1)
    if monday.month == friday.month:
        return f"{monday.day}–{friday.day} {MONTH_NAMES[friday.month]}"
    return (
        f"{monday.day} {MONTH_NAMES[monday.month]} – "
        f"{friday.day} {MONTH_NAMES[friday.month]}"
    )


def slug_candidates(monday: date) -> list[str]:
    """Possibili URL slug dell'articolo "le trame dal X al Y" di una settimana."""
    friday = monday + timedelta(days=EPISODE_DAYS - 1)
    d1, d2 = monday.day, friday.day
    m1, m2 = MONTH_NAMES[monday.month], MONTH_NAMES[friday.month]
    if monday.month == friday.month:
        spans = [f"{d1}-al-{d2}-{m2}"]
        if d2 in (8, 11):  # elisione italiana: "all'8", "all'11"
            spans.insert(0, f"{d1}-all{d2}-{m2}")
    else:
        spans = [f"{d1}-{m1}-al-{d2}-{m2}"]
        if d2 in (8, 11):
            spans.insert(0, f"{d1}-{m1}-all{d2}-{m2}")
    years = []
    for y in (friday.year, monday.year):
        if y not in years:
            years.append(y)
    return [f"{span}-{y}" for span in spans for y in years]


def parse_week_span(text: str) -> tuple[date, date] | None:
    """Estrae (lunedì, venerdì) da un titolo o da uno slug."""
    match = _WEEK_SPAN.search(text.replace("-", " ").replace("’", "'"))
    if not match:
        return None
    d1, m1, d2, m2, year = match.groups()
    m2n = MONTHS.get(_fold(m2))
    if not m2n:
        return None
    m1n = MONTHS.get(_fold(m1)) if m1 else m2n
    if not m1n:
        return None
    try:
        end = date(int(year), m2n, int(d2))
        start_year = int(year) - 1 if m1n > m2n else int(year)
        start = date(start_year, m1n, int(d1))
    except ValueError:
        return None
    return start, end


def extract_week_links(html: str, base: str) -> dict[date, str]:
    """Dalla pagina tag restituisce {lunedì: url} degli articoli delle trame."""
    soup = BeautifulSoup(html, "html.parser")
    found: dict[date, str] = {}
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "un-posto-al-sole-le-trame-dal-" not in href:
            continue
        span = parse_week_span(href.rstrip("/").rsplit("/", 1)[-1])
        if not span:
            continue
        url = href if href.startswith("http") else base.rstrip("/") + "/" + href.lstrip("/")
        found.setdefault(span[0], url.split("#")[0])
    return found


# -------------------------------------------------------------------- testi
def make_excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if end >= limit * 0.5:
        return cut[: end + 1]
    return cut[: cut.rfind(" ")].rstrip(",;:") + "…"


def _heading_date(match: re.Match[str], monday: date) -> date | None:
    month = MONTHS.get(_fold(match.group(3)))
    if not month:
        return None
    year = monday.year + (1 if month < monday.month - 6 else 0)
    try:
        return date(year, month, int(match.group(2)))
    except ValueError:
        return None


def parse_week_article(html: str, monday: date, url: str, source: str) -> dict[str, Any] | None:
    """Estrae titolo, data di pubblicazione e trama giornaliera di un articolo."""
    soup = BeautifulSoup(html, "html.parser")
    days: list[dict[str, Any]] = []
    for h2 in soup.find_all("h2"):
        match = _DAY_HEADING.match(_fold(h2.get_text(" ", strip=True)))
        if not match:
            continue
        day = _heading_date(match, monday)
        if not day:
            continue
        parts: list[str] = []
        for sib in h2.find_next_siblings():
            if sib.name in ("h1", "h2", "h3"):
                break
            if sib.name == "p":
                txt = clean(sib.get_text(" ", strip=True))
                if txt:
                    parts.append(txt)
            if len(parts) >= 3:
                break
        if not parts:  # struttura annidata: prendi il primo paragrafo successivo
            nxt = h2.find_next("p")
            if nxt:
                parts.append(clean(nxt.get_text(" ", strip=True)))
        text = " ".join(parts)
        if text:
            days.append(
                {
                    "date": day.isoformat(),
                    "weekday": WEEKDAYS[day.weekday()] if day.weekday() < 5 else "",
                    "excerpt": make_excerpt(text),
                }
            )
    if not days:
        return None
    title = soup.find("h1")
    published = soup.find("meta", attrs={"property": "article:published_time"})
    friday = monday + timedelta(days=EPISODE_DAYS - 1)
    return {
        "start": monday.isoformat(),
        "end": friday.isoformat(),
        "label": week_label(monday),
        "available": True,
        "title": clean(title.get_text(" ", strip=True)) if title else "",
        "published": published.get("content", "") if published else "",
        "url": url,
        "source": source,
        "days": sorted(days, key=lambda d: d["date"]),
    }


def empty_week(monday: date) -> dict[str, Any]:
    friday = monday + timedelta(days=EPISODE_DAYS - 1)
    return {
        "start": monday.isoformat(),
        "end": friday.isoformat(),
        "label": week_label(monday),
        "available": False,
        "title": "",
        "published": "",
        "url": "",
        "source": "",
        "days": [],
    }


# ------------------------------------------------------------------ notizie
def _unwrap_link(link: str) -> str:
    """I link di Bing News sono redirect (apiclick.aspx?url=...): estrae l'originale."""
    parsed = urlparse(link)
    if parsed.netloc.endswith("bing.com") and "apiclick" in parsed.path:
        target = parse_qs(parsed.query).get("url", [""])[0]
        if target.startswith(("http://", "https://")):
            return target
    return link


def merge_news(lists: list[list[dict[str, Any]]], limit: int) -> list[dict[str, Any]]:
    """Unisce più elenchi di notizie: deduplica per titolo, più recenti prima."""
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for items in lists:
        for item in items:
            key = _fold(item["title"])
            if key not in seen:
                seen.add(key)
                merged.append(item)
    merged.sort(key=lambda i: i["published"], reverse=True)
    return merged[:limit]


def parse_news_rss(xml_text: str, limit: int) -> list[dict[str, Any]]:
    """Legge il feed RSS di Google News: titolo, testata, link, data."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in root.iter("item"):
        raw_title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        if not raw_title or not link:
            continue
        link = _unwrap_link(link)
        source_el = item.find("source")
        if source_el is None:  # Bing: <News:Source> con namespace
            source_el = next((c for c in item if c.tag.rsplit("}", 1)[-1].lower() == "source"), None)
        source = clean(source_el.text) if source_el is not None else ""
        title = raw_title
        if source and raw_title.endswith(f" - {source}"):
            title = raw_title[: -len(source) - 3]
        elif " - " in raw_title:
            title, source = raw_title.rsplit(" - ", 1)
        key = _fold(title)
        if key in seen:
            continue
        seen.add(key)
        try:
            when = parsedate_to_datetime(item.findtext("pubDate") or "")
            when = when.astimezone(timezone.utc) if when.tzinfo else when.replace(tzinfo=timezone.utc)
            published = when.isoformat()
        except (TypeError, ValueError):
            published = ""
        items.append(
            {"title": title.strip(), "source": source.strip(), "url": link, "published": published}
        )
    items.sort(key=lambda i: i["published"], reverse=True)
    return items[:limit]
