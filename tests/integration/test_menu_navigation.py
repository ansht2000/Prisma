"""Integration tests for booting into the menu and navigating out of it,
driving the real app loop in a background thread.

These cover the scene-swap plumbing in app.py -- that a menu action actually
replaces the running scene, or shuts the loop down -- which the MenuScene unit
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
from menu import MenuScene
from mirror import Mirror

pytestmark = pytest.mark.integration

SETTLE = 0.25


def post(event_type: int, **kwargs: Any) -> None:
    pygame.event.post(pygame.event.Event(event_type, kwargs))


def click(pos: tuple[float, float]) -> None:
    post(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)
    time.sleep(SETTLE)


@pytest.fixture
def menu_app() -> Iterator[threading.Thread]:
    """Boots the real app loop on the menu, as main() does."""
    # SandboxScene sets this class attribute when it is constructed, so clearing
    # it first makes "did we actually reach the sandbox?" observable.
    if hasattr(Mirror, "containers"):
        del Mirror.containers

    thread = threading.Thread(target=lambda: app.run(MenuScene), daemon=True)
    thread.start()

    for _ in range(100):
        if pygame.display.get_surface():
            break
        time.sleep(0.05)
    time.sleep(0.3)

    yield thread

    # A test that clicked Quit has already shut the loop down and called
    # pygame.quit(), which leaves the event system unusable -- only ask a
    # still-running loop to stop.
    if thread.is_alive() and pygame.display.get_init():
        post(pygame.QUIT)
    thread.join(timeout=3)


def button_position(label: str) -> tuple[float, float]:
    """Where the running menu drew a given button.

    Layout is deterministic from the surface size, so a throwaway MenuScene on
    the same surface reports the same rects as the one the app is running.
    """
    surface = pygame.display.get_surface()
    assert surface is not None
    probe = MenuScene(surface)
    for button in probe.buttons:
        if button.label == label:
            return button.rect.center
    raise AssertionError(f"no button labelled {label!r}")


def test_the_app_starts_on_the_menu_not_the_sandbox(menu_app: threading.Thread) -> None:
    assert not hasattr(Mirror, "containers")
    assert menu_app.is_alive()


def test_clicking_sandbox_switches_the_running_scene(menu_app: threading.Thread) -> None:
    click(button_position("Sandbox"))

    # Only SandboxScene.__init__ wires up the sprite groups
    assert hasattr(Mirror, "containers")
    assert menu_app.is_alive()


def test_clicking_a_disabled_option_leaves_the_menu_running(menu_app: threading.Thread) -> None:
    click(button_position("Level Select"))
    click(button_position("Settings"))

    assert not hasattr(Mirror, "containers")
    assert menu_app.is_alive()


def test_clicking_quit_shuts_the_app_down(menu_app: threading.Thread) -> None:
    click(button_position("Quit"))

    menu_app.join(timeout=3)
    assert not menu_app.is_alive()
