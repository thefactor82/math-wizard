import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import importlib.util
from pathlib import Path
import pygame

MODULE_PATH = Path(__file__).resolve().parents[1] / "math-wizard.py"
SPEC = importlib.util.spec_from_file_location("mathwizard_main", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _make_sprite(size=80, border=16):
    sprite = pygame.Surface((size, size), pygame.SRCALPHA)
    sprite.fill((0, 0, 0, 0))
    pygame.draw.rect(sprite, (0, 0, 255, 255), (border, border, size - border * 2, size - border * 2))
    return sprite


def _screen():
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((400, 400))
    surf = pygame.Surface((400, 400))
    surf.fill((255, 0, 0))
    return surf


def test_blit_faded_keeps_transparency():
    pygame.init()
    screen = _screen()
    game = MODULE.Game.__new__(MODULE.Game)
    game.screen = screen

    sprite = _make_sprite().convert_alpha(screen)
    game._blit_faded(sprite, (10, 10), 128)
    assert screen.get_at((12, 12))[:3] == (255, 0, 0)
    centre = screen.get_at((50, 50))
    assert 0 < centre[0] < 255 and centre[2] > 0


def test_blit_faded_does_not_mutate_source():
    pygame.init()
    screen = _screen()
    game = MODULE.Game.__new__(MODULE.Game)
    game.screen = screen

    sprite = _make_sprite().convert_alpha(screen)
    game._blit_faded(sprite, (10, 10), 128)
    game._blit_faded(sprite, (10, 10), 60)

    screen.fill((255, 0, 0))
    screen.blit(sprite, (10, 10))
    assert screen.get_at((12, 12))[:3] == (255, 0, 0)
    assert screen.get_at((50, 50))[:3] == (0, 0, 255)
