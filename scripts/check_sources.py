"""Controlla che le fonti reali siano ancora leggibili dai parser.

Uso:  python scripts/check_sources.py            # rete reale (CI settimanale)
      python scripts/check_sources.py --offline  # usa le fixture dei test

Esce con codice 1 se un parser non riesce piu' a leggere la fonte.
"""
from __future__ import annotations

import importlib.util
import sys
import types
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "custom_components" / "upas"
FIX = ROOT / "tests" / "fixtures"


def _load():
    """Carica const.py e parsers.py senza importare Home Assistant."""
    pkg = types.ModuleType("upas_pkg")
    pkg.__path__ = [str(PKG)]
    sys.modules["upas_pkg"] = pkg
    mods = {}
    for name in ("const", "parsers"):
        spec = importlib.util.spec_from_file_location(f"upas_pkg.{name}", PKG / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f"upas_pkg.{name}"] = mod
        spec.loader.exec_module(mod)
        mods[name] = mod
    return mods["const"], mods["parsers"]


def _get(url: str, offline: str | None) -> str:
    if offline:
        return (FIX / offline).read_text()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HomeAssistant-UPAS-check)"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return resp.read().decode("utf-8", "replace")


def main() -> int:
    offline = "--offline" in sys.argv
    const, parsers = _load()
    problems: list[str] = []

    tag = _get(const.PLOTS_TAG_URL, "tag_page.html" if offline else None)
    links = parsers.extract_week_links(tag, const.PLOTS_BASE)
    if not links:
        problems.append("pagina tag Sorrisi: nessun link alle trame trovato")
    else:
        monday = max(links)
        html = _get(links[monday], "week_19_23_ott.html" if offline else None)
        week = parsers.parse_week_article(html, monday, links[monday], const.PLOTS_SOURCE_NAME)
        if not week or len(week["days"]) < 4:
            problems.append(f"articolo {links[monday]}: giorni letti = {len((week or {}).get('days', []))} (attesi 5)")
        else:
            print(f"OK trame {week['label']}: {len(week['days'])} giorni")

    for name, url in const.NEWS_FEEDS.items():
        fixture = {"google": "news.xml", "bing": "news_bing.xml"}[name] if offline else None
        try:
            items = parsers.parse_news_rss(_get(url, fixture), 10)
        except Exception as err:  # noqa: BLE001
            problems.append(f"feed {name}: {err}")
            continue
        if not items:
            problems.append(f"feed {name}: nessuna notizia")
        else:
            print(f"OK feed {name}: {len(items)} notizie")

    for p in problems:
        print("PROBLEMA:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
