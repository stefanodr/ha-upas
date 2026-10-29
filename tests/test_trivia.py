from datetime import date

from custom_components.upas.trivia import load_characters, load_trivia, pick_character, pick_trivia

ITEMS = load_trivia()


def test_dataset_is_well_formed():
    assert len(ITEMS) >= 20
    ids = [i["id"] for i in ITEMS]
    assert len(ids) == len(set(ids))
    for i in ITEMS:
        assert i["url"].startswith("https://") and i["source"] and i["title"]
        assert 20 < len(i["text"]) <= 300
        if "on" in i:
            assert len(i["on"]) == 5 and i["on"][2] == "-"


def test_anniversary_has_priority():
    assert pick_trivia(ITEMS, date(2026, 10, 21))["id"] == "prima-puntata"
    assert pick_trivia(ITEMS, date(2027, 7, 29))["id"] == "seimila"


def test_rotation_is_daily_and_matches_card():
    a = pick_trivia(ITEMS, date(2026, 10, 27))
    b = pick_trivia(ITEMS, date(2026, 10, 28))
    assert a["id"] != b["id"]
    # la rotazione e' deterministica: stesso giorno, stessa pillola (anche nella card)
    assert a == pick_trivia(ITEMS, date(2026, 10, 27))
    assert pick_trivia(ITEMS, date(2026, 10, 27), skip=1)["id"] == b["id"]
    assert pick_trivia([], date(2026, 10, 27)) is None


def test_missing_file_gives_empty_list(tmp_path):
    assert load_trivia(tmp_path / "nope.json") == []


CHARS = load_characters()


def test_characters_dataset_is_well_formed():
    assert len(CHARS) >= 10
    ids = [c["id"] for c in CHARS]
    assert len(ids) == len(set(ids))
    for c in CHARS:
        assert c["url"].startswith("https://") and c["source"]
        assert c["name"] and c["actor"] and c["role"]
        assert 20 < len(c["caption"]) <= 350
        assert "/" not in c.get("photo", "") and "." not in c.get("photo", "")  # solo il nome del file, senza percorso


def test_character_prefers_those_in_todays_plot():
    plot = "Eduardo torna a farsi vivo e sconvolge i piani di tutti."
    who, cited = pick_character(CHARS, plot, date(2026, 10, 29))
    assert cited and who["id"] == "eduardo"
    # alias: Ferri e' citato per cognome
    who, cited = pick_character(CHARS, "Ferri prepara la sua mossa.", date(2026, 10, 29))
    assert cited and who["id"] == "ferri"


def test_character_rotation_when_nobody_cited():
    a, cited = pick_character(CHARS, "", date(2026, 10, 29))
    b, _ = pick_character(CHARS, "", date(2026, 10, 30))
    assert not cited and a["id"] != b["id"]
    assert pick_character([], "x", date(2026, 10, 29)) is None
