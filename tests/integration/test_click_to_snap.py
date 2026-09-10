"""Integration tests driving the real app loop in a background thread, posting
synthetic pygame events the way an actual mouse/keyboard would. These exercise
the click-vs-drag disambiguation and InputBox routing wired into
SandboxScene, not just the InputBox class in isolation (see
tests/unit/test_input_box.py for that).

The app boots into the menu, so these start the loop on SandboxScene directly
rather than clicking through it -- tests/unit/test_menu.py covers that step.
"""
import os
import threading
import time
from typing import Any, Iterator

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

import app
from mirror import Mirror
from sandbox import SandboxScene

pytestmark = pytest.mark.integration

SETTLE = 0.15


def post(event_type: int, **kwargs: Any) -> None:
    pygame.event.post(pygame.event.Event(event_type, kwargs))


def type_digits(text: str) -> None:
    for char in text:
        post(pygame.KEYDOWN, key=ord(char), unicode=char)
    time.sleep(SETTLE)


def press_release(pos_down: tuple[float, float], pos_up: tuple[float, float]) -> None:
    post(pygame.MOUSEBUTTONDOWN, pos=pos_down, button=1)
    time.sleep(SETTLE)
    post(pygame.MOUSEBUTTONUP, pos=pos_up, button=1)
    time.sleep(SETTLE)


@pytest.fixture
def running_game() -> Iterator[pygame.Surface]:
    """Starts the real app loop on SandboxScene in a background thread and
    tears it down afterwards by posting a QUIT event."""
    thread = threading.Thread(target=lambda: app.run(SandboxScene), daemon=True)
    thread.start()

    for _ in range(100):
        if hasattr(Mirror, "containers") and pygame.display.get_surface():
            break
        time.sleep(0.05)
    time.sleep(0.3)

    surface = pygame.display.get_surface()
    assert surface is not None
    yield surface

    post(pygame.QUIT)
    thread.join(timeout=3)


def spawn_mirror(screen: pygame.Surface, x: float = 400, y: float = 300) -> Mirror:
    mirror = Mirror(x, y, screen)  # joins the live sprite groups via .containers
    time.sleep(0.3)
    return mirror


class TestClickOpensAndSnaps:
    def test_a_click_opens_the_box_and_enter_snaps_the_value(self, running_game: pygame.Surface) -> None:
        screen = running_game
        mirror = spawn_mirror(screen)
        mirror.set_orientation(0)
        assert mirror.rect is not None
        spot = mirror.rect.center

        press_release(spot, spot)
        type_digits("77")
        post(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")
        time.sleep(0.25)

        assert mirror.orientation == 77


class TestDragDoesNotOpenTheBox:
    def test_dragging_past_the_click_threshold_leaves_the_box_closed(self, running_game: pygame.Surface) -> None:
        screen = running_game
        mirror = spawn_mirror(screen)
        mirror.set_orientation(0)
        assert mirror.rect is not None
        spot = mirror.rect.center

        press_release(spot, (spot[0] + 60, spot[1] + 60))
        # With no box open, these keystrokes must go nowhere.
        type_digits("123")
        post(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")
        time.sleep(0.25)

        assert mirror.orientation == 0


class TestClickingOffTheBox:
    def test_click_away_from_the_box_commits_the_typed_value(self, running_game: pygame.Surface) -> None:
        screen = running_game
        mirror = spawn_mirror(screen)
        mirror.set_orientation(0)
        assert mirror.rect is not None
        spot = mirror.rect.center

        press_release(spot, spot)
        type_digits("42")
        far_away = (900, 600)
        post(pygame.MOUSEBUTTONDOWN, pos=far_away, button=1)
        time.sleep(0.25)

        assert mirror.orientation == 42

    def test_the_dismissing_click_does_not_start_a_new_drag(self, running_game: pygame.Surface) -> None:
        screen = running_game
        mirror = spawn_mirror(screen)
        mirror.set_orientation(0)
        assert mirror.rect is not None
        spot = mirror.rect.center

        press_release(spot, spot)
        type_digits("42")
        post(pygame.MOUSEBUTTONDOWN, pos=(900, 600), button=1)
        time.sleep(0.25)
        position_after_commit = (mirror.pos_x, mirror.pos_y)
        time.sleep(0.2)

        assert (mirror.pos_x, mirror.pos_y) == position_after_commit
