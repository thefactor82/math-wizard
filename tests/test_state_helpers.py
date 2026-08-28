import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "math-wizard.py"
SPEC = importlib.util.spec_from_file_location("mathwizard_main", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_normalize_story_entry_keeps_only_modern_keys():
    entry = {"type": "level", "background": "forest1", "monsters": [1, 2], "player_in": "sx"}

    normalized = MODULE.normalize_story_entry(entry)
    assert normalized["type"] == "level"
    assert normalized["background"] == "forest1"
    assert normalized["monsters"] == [1, 2]
    assert normalized["player_in"] == "sx"
    assert "tipo" not in normalized
    assert "bg" not in normalized


def test_story_level_index_tracks_the_requested_level_entry():
    story_entries = [
        {"type": "text", "background": "village"},
        {"type": "scene", "background": "field"},
        {"type": "level", "background": "forest1"},
        {"type": "level", "background": "home"},
        {"type": "level", "background": "woods"},
    ]

    assert MODULE.story_level_index_for_initial_level(story_entries, 0) == 2
    assert MODULE.story_level_index_for_initial_level(story_entries, 1) == 3
    assert MODULE.story_level_index_for_initial_level(story_entries, 99) == 4


def test_show_story_sets_target_background_before_fade():
    game = MODULE.Game.__new__(MODULE.Game)
    game.story_entries = [{"type": "level", "background": "forest1"}]
    game.story_idx = 0
    game.story_is_level = False
    game.state = MODULE.GAME_STATE_STORY
    game.story_next_bg = None
    game.game_bg = MODULE.Game.__new__(MODULE.Game).bg if hasattr(MODULE.Game.__new__(MODULE.Game), "bg") else None
    game.bg = object()
    game.story_fade_alpha = 80
    game.story_fade_color = (0, 0, 0)
    game.story_phase = "exit"
    game.level_is_scene = False
    game.current_music = "background"
    game.player_in_dir = "sx"
    game.player_out_dir = "dx"
    game.player_entrance = True
    game.monster_in_dir = "dx"
    game.player_flip = False
    game.player_stand_x = 112
    game.story_monsters = []
    game.story_flying_monsters = []
    game.boss_active = False
    game.level_scene_before = None
    game.level_scene_after = None
    game.story_text_full = ""
    game.story_characters_shown = 0
    game.story_object_img = None
    game.story_object_alpha = 0
    game.story_first_step = False
    game.set_state = lambda state, reset_scene=False: setattr(game, "state", MODULE.normalize_game_state(state))
    game._ensure_monsters = lambda monsters: None
    game._get_bg = lambda name: {"forest1": "forest-surface"}.get(name)
    game.switch_music = lambda target: None

    game.show_story()

    assert game.story_next_bg == "forest-surface"
    assert game.game_bg == "forest-surface"


def test_state_helpers_keep_canonical_values():
    assert MODULE.GAME_STATE_SPLASH == "splash"
    assert MODULE.GAME_STATE_PROGRESS == "progress"
    assert MODULE.SCENE_PHASE_ENTER == "enter"
    assert MODULE.normalize_scene_phase("dialogue") == "dialogue"
    assert MODULE.normalize_scene_phase("enter") == "enter"
    assert MODULE.normalize_scene_phase("exit") == "exit"
    assert MODULE.normalize_game_state("progress") == "progress"
    assert MODULE.normalize_game_state("level_complete") == "level_complete"
    assert MODULE.normalize_game_state("scene_end") == "scene_end"
