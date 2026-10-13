import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "math-wizard.py"
SPEC = importlib.util.spec_from_file_location("mathwizard_main", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_game(level=1, timeout_limit=6, recent_times=None, progress=1, num_levels=5):
    game = MODULE.Game.__new__(MODULE.Game)
    game.tutorial_active = False
    game.level = level
    game.num_story_levels = num_levels
    game.timeout_limit = timeout_limit
    game.config_story_operation = "moltiplicazione"
    game.story_progress = {"moltiplicazione": progress}
    game.story_completed = {}
    game.monster_times = list(recent_times if recent_times is not None else [1.0] * 16)
    game.initial_level = 0
    game.return_to_game = False
    game.state = None

    def set_initial_level(value):
        game.initial_level = value

    game.set_initial_level = set_initial_level
    game.save_profile_config = lambda: None
    return game


def test_would_drop_true_when_fast_and_above_floor():
    game = make_game(level=1, timeout_limit=6, recent_times=[1.0] * 16, progress=1)
    assert game._story_timeout_would_drop() is True


def test_would_drop_false_at_floor_even_with_fast_answers():
    game = make_game(level=1, timeout_limit=5, recent_times=[0.5] * 16, progress=1)
    assert game._story_timeout_would_drop() is False


def test_would_drop_false_on_last_level():
    game = make_game(level=4, timeout_limit=6, recent_times=[0.5] * 16, progress=4)
    assert game._story_timeout_would_drop() is False


def test_would_drop_true_when_replaying_old_level():
    game = make_game(level=1, timeout_limit=6, recent_times=[0.5] * 16, progress=5)
    assert game._story_timeout_would_drop() is True


def test_would_drop_false_when_answers_slow():
    game = make_game(level=1, timeout_limit=6, recent_times=[10.0] * 16, progress=1)
    assert game._story_timeout_would_drop() is False


def test_advance_lowers_to_floor_not_below():
    game = make_game(level=1, timeout_limit=6, recent_times=[1.0] * 16, progress=1)
    game._advance_level_complete()
    assert game.timeout_limit == 5
    assert game.level == 2


def test_advance_keeps_five_when_already_at_floor():
    game = make_game(level=1, timeout_limit=5, recent_times=[0.5] * 16, progress=1)
    game._advance_level_complete()
    assert game.timeout_limit == 5


def test_advance_lowers_timeout_when_replaying_old_level():
    game = make_game(level=1, timeout_limit=6, recent_times=[0.5] * 16, progress=5)
    game._advance_level_complete()
    assert game.timeout_limit == 5
    assert game.story_progress["moltiplicazione"] == 5
