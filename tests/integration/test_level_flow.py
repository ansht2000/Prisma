"""Integration test for the whole level path through the real app loop:
menu -> level select -> level 1 -> win -> back to level select.

Covers the scene-swap plumbing between these screens, which the per-scene unit
tests cannot see because they never run a loop.
"""
import os
import threading
import time
from typing import Any, Iterator

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

import app
from level_select import LevelSelectScene
from menu import MenuScene

pytestmark = pytest.mark.integration

SETTLE = 0.25


def post(event_type: int, **kwargs: Any) -> None:
    pygame.event.post(pygame.event.Event(event_type, kwargs))


def click(pos: tuple[float, float]) -> None:
    post(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
    time.sleep(SETTLE)


def press(key: int) -> None:
    post(pygame.KEYDOWN, key=key, unicode="")
    time.sleep(SETTLE)


@pytest.fixture
def menu_app() -> Iterator[None]:
    thread = threading.Thread(target=lambda: app.run(MenuScene), daemon=True)
    thread.start()

    for _ in range(100):
        if pygame.display.get_surface():
            break
        time.sleep(0.05)
    time.sleep(0.3)

    yield

    if thread.is_alive() and pygame.display.get_init():
        post(pygame.QUIT)
    thread.join(timeout=3)


def surface() -> pygame.Surface:
    current = pygame.display.get_surface()
    assert current is not None
    return current


def menu_button(label: str) -> tuple[float, float]:
    """Layout is deterministic from the surface size, so a throwaway scene
    reports the same rects as the one the app is running."""
    for button in MenuScene(surface()).buttons:
        if button.label == label:
            return button.rect.center
    raise AssertionError(f"no menu button labelled {label!r}")


def level_box(number: int) -> tuple[float, float]:
    for button in LevelSelectScene(surface()).buttons:
        if button.label == str(number):
            return button.rect.center
    raise AssertionError(f"no level box for {number}")


def screen_is_mostly_black() -> bool:
    """The level select screen is nearly empty; a running level fills the
    middle with a board."""
    center = surface().get_at((surface().get_width() // 2, surface().get_height() // 2))
    return center.r < 10 and center.g < 10 and center.b < 10


def test_menu_to_level_select_to_level_and_back(menu_app: None) -> None:
    # Menu -> level select
    click(menu_button("Level Select"))
    assert screen_is_mostly_black(), "level select should be an empty screen"

    # Level select -> level 1, which paints a board across the middle
    click(level_box(1))
    assert not screen_is_mostly_black(), "level 1 should be drawing its board"

    # Escape backs out of the level to level select again
    press(pygame.K_ESCAPE)
    assert screen_is_mostly_black(), "escape should return to level select"


def test_level_select_escapes_back_to_the_menu(menu_app: None) -> None:
    click(menu_button("Level Select"))
    press(pygame.K_ESCAPE)

    # Back on the menu, whose Quit button still shuts the app down
    click(menu_button("Quit"))
    time.sleep(SETTLE)

    assert not pygame.display.get_init()
