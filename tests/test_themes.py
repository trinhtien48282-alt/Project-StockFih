from stockfih.ui.themes import PIECE_THEMES, SQUARE_THEMES


def test_themes_are_distinguishable():
    for t in SQUARE_THEMES.values():
        assert t.light != t.dark
    for t in PIECE_THEMES.values():
        assert t.white != t.black
