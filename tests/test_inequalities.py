import importlib.util
import random
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "math-wizard.py"
SPEC = importlib.util.spec_from_file_location("mathwizard_main", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_fixed_game(correct=42, pool_a=None, lo=0, hi=100, active=True):
    game = MODULE.Game.__new__(MODULE.Game)
    game.mode = "fixed"
    game.tutorial_active = False
    game.config_plus_inequalities = active
    game.expected_result = correct
    game.pool_a = list(pool_a if pool_a is not None else [0, 1, 3, 5, 7])
    game.config = {"risultato_minimo": lo, "risultato_massimo": hi}
    return game


def make_auto_game(correct=42, pool_a=None, lo=0, hi=100):
    game = MODULE.Game.__new__(MODULE.Game)
    game.mode = "auto"
    game.tutorial_active = False
    game.config_plus_inequalities = True
    game.expected_result = correct
    game.levels = [{
        "pool_a": list(pool_a if pool_a is not None else [0, 1, 3, 5, 7]),
        "min_value": lo,
        "max_value": hi,
    }]
    game.effective_level = lambda: 0
    return game


def test_inactive_clears_fields():
    game = make_fixed_game(active=False)
    game.inequality_symbol = "<"
    game.inequality_value = 5
    game.expected_choice = True
    game._apply_inequality()
    assert game.inequality_symbol is None
    assert game.inequality_value is None
    assert game.expected_choice is None


def test_symbol_and_choice_are_consistent():
    random.seed(1)
    for _ in range(300):
        game = make_fixed_game(correct=42, pool_a=list(range(0, 10)), lo=0, hi=200)
        game._apply_inequality()
        assert game.inequality_symbol in ("<", ">")
        value = game.inequality_value
        if game.inequality_symbol == "<":
            assert game.expected_choice is (42 < value)
        else:
            assert game.expected_choice is (42 > value)


def test_value_within_result_range():
    random.seed(2)
    for _ in range(300):
        game = make_fixed_game(correct=42, pool_a=list(range(0, 200)), lo=30, hi=50)
        game._apply_inequality()
        assert 30 <= game.inequality_value <= 50
        assert game.inequality_value >= 0


def test_value_comes_from_pool_offset():
    random.seed(3)
    pool = [0, 2, 4, 6, 8]
    allowed = set()
    for x in pool:
        for sign in (1, -1):
            allowed.add(42 + sign * x)
    for _ in range(300):
        game = make_fixed_game(correct=42, pool_a=pool, lo=-99, hi=199)
        game._apply_inequality()
        assert game.inequality_value in allowed


def test_zero_only_pool_allows_coincide():
    game = make_fixed_game(correct=42, pool_a=[0], lo=0, hi=199)
    for _ in range(20):
        game._apply_inequality()
        assert game.inequality_value == 42
        assert game.expected_choice is False


def test_fallback_when_no_candidate_in_range():
    # nessun offset valido nel range stretto -> fallback al risultato corretto
    game = make_fixed_game(correct=100, pool_a=[50], lo=0, hi=10)
    game._apply_inequality()
    assert game.inequality_value == 100
    assert game.expected_choice is False


def test_story_mode_uses_level_pool_and_range():
    random.seed(4)
    for _ in range(300):
        game = make_auto_game(correct=42, pool_a=[0, 1, 2, 3], lo=40, hi=45)
        game._apply_inequality()
        assert 40 <= game.inequality_value <= 45


def test_float_result_skips_inequality():
    game = make_fixed_game(correct=7.5, pool_a=[1, 2], lo=0, hi=100)
    game._apply_inequality()
    assert game.inequality_value is None
    assert game.expected_choice is None


def test_integer_float_result_is_accepted():
    game = make_fixed_game(correct=8.0, pool_a=[0], lo=0, hi=100)
    game._apply_inequality()
    assert game.inequality_value == 8


def test_choice_options_and_rects_geometry():
    game = MODULE.Game.__new__(MODULE.Game)
    options = game._choice_options()
    assert options == [("VERO", True), ("FALSO", False)]
    rects = game._choice_button_rects()
    assert len(rects) == 2
    assert rects[0].right < rects[1].left
    assert rects[0].width == 240 and rects[0].height == 92
    assert rects[0].centery == 232
