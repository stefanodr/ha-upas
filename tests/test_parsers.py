from datetime import date
from pathlib import Path

from custom_components.upas import parsers as p

FIX = Path(__file__).parent / "fixtures"
URL = "https://www.sorrisi.com/x/"


def test_reference_monday_weekend_rolls_forward():
    assert p.reference_monday(date(2026, 10, 22)) == date(2026, 10, 19)  # giovedì
    assert p.reference_monday(date(2026, 10, 24)) == date(2026, 10, 26)  # sabato
    assert p.reference_monday(date(2026, 10, 25)) == date(2026, 10, 26)  # domenica


def test_slug_candidates():
    assert p.slug_candidates(date(2026, 10, 19)) == ["19-al-23-ottobre-2026"]
    assert p.slug_candidates(date(2026, 9, 7))[0] == "7-all11-settembre-2026"
    assert "7-al-11-settembre-2026" in p.slug_candidates(date(2026, 9, 7))
    assert p.slug_candidates(date(2026, 8, 31)) == ["31-agosto-al-4-settembre-2026"]
    cross_year = p.slug_candidates(date(2026, 12, 28))
    assert "28-dicembre-al-1-gennaio-2027" in cross_year


def test_parse_week_span_titles_and_slugs():
    assert p.parse_week_span("Un posto al sole, le trame dal 19 al 23 ottobre 2026") == (date(2026, 10, 19), date(2026, 10, 23))
    assert p.parse_week_span("le trame dal 7 all'11 settembre 2026") == (date(2026, 9, 7), date(2026, 9, 11))
    assert p.parse_week_span("un-posto-al-sole-le-trame-dal-7-all11-settembre-2026") == (date(2026, 9, 7), date(2026, 9, 11))
    assert p.parse_week_span("dal 31 agosto al 4 settembre 2026") == (date(2026, 8, 31), date(2026, 9, 4))
    assert p.parse_week_span("dal 28 dicembre al 1 gennaio 2027") == (date(2026, 12, 28), date(2027, 1, 1))
    assert p.parse_week_span("titolo qualsiasi") is None


def test_extract_week_links():
    links = p.extract_week_links((FIX / "tag_page.html").read_text(), "https://www.sorrisi.com")
    assert set(links) == {date(2026, 10, 19), date(2026, 9, 7), date(2026, 8, 31)}
    assert links[date(2026, 9, 7)].startswith("https://www.sorrisi.com/tv/soap/")


def test_parse_week_article():
    week = p.parse_week_article((FIX / "week_19_23_ott.html").read_text(), date(2026, 10, 19), URL, "TV Sorrisi e Canzoni")
    assert week and week["available"]
    assert [d["date"] for d in week["days"]] == ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]
    assert week["days"][0]["weekday"] == "lunedì"
    assert week["label"] == "19–23 ottobre"
    assert week["published"].startswith("2026-10-17")
    for d in week["days"]:
        assert len(d["excerpt"]) <= 285
    # il paragrafo "Leggi anche" non deve finire nell'ultimo giorno
    assert "correlati" not in week["days"][-1]["excerpt"]
    assert "Spreaker" not in week["days"][-1]["excerpt"]


def test_parse_week_article_garbage():
    assert p.parse_week_article("<html><body><h2>Altro</h2><p>x</p></body></html>", date(2026, 10, 19), URL, "s") is None


def test_make_excerpt_cuts_on_sentence():
    text = "Prima frase completa e abbastanza lunga da contare. " * 10
    out = p.make_excerpt(text, 120)
    assert out.endswith(".") and len(out) <= 120


def test_parse_news_rss():
    items = p.parse_news_rss((FIX / "news.xml").read_text(), 10)
    titles = [i["title"] for i in items]
    assert titles.count("Un posto al sole, Marina paga il silenzio") == 1  # dedup
    assert items[0]["source"] == "Napolike"  # più recente per primo
    assert 'Attore di Upas: "Dopo 30 anni - ancora emozioni"' == items[0]["title"]
    assert p.parse_news_rss("non xml", 5) == []
    assert len(p.parse_news_rss((FIX / "news.xml").read_text(), 2)) == 2


def test_bing_rss_and_merge():
    bing = p.parse_news_rss((FIX / "news_bing.xml").read_text(), 10)
    assert bing[0]["url"] == "https://www.tvsoap.it/b"
    assert bing[0]["source"] == "TVSoap"
    google = p.parse_news_rss((FIX / "news.xml").read_text(), 10)
    merged = p.merge_news([google, bing], 10)
    titles = [i["title"] for i in merged]
    assert titles.count("Un posto al sole, Marina paga il silenzio") == 1
    assert merged[0]["title"] == "Upas, tornano Eduardo e Ferri"
    assert len(p.merge_news([google, bing], 2)) == 2
