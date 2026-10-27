from datetime import date

from custom_components.upas.trivia import load_trivia, pick_trivia

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
    # stesso valore mostrato dalla card il 27/10/2026 (pillola 8/23)
    assert a["id"] == "covid"
    assert pick_trivia(ITEMS, date(2026, 10, 27), skip=1)["id"] == b["id"]
    assert pick_trivia([], date(2026, 10, 27)) is None


def test_missing_file_gives_empty_list(tmp_path):
    assert load_trivia(tmp_path / "nope.json") == []
