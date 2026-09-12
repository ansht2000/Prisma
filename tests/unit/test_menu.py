"""Unit tests for MenuScene: option-to-button wiring, click routing, disabled
entries, and that the screen is genuinely driven by its option list.

No app loop involved -- events are constructed directly and fed to
handle_event(). tests/integration/test_click_to_snap.py covers the sandbox
once it is running.
"""
import pygame
import pytest

from level_editor import LevelEditorScene
from level_select import LevelSelectScene
from menu import MenuOption, MenuScene, MENU_OPTIONS
from sandbox import SandboxScene

pytestmark = pytest.mark.unit


def click_event(pos: tuple[float, float]) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def motion_event(pos: tuple[float, float]) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos})


def click_label(menu: MenuScene, label: str) -> None:
    """Clicks the button carrying the given label."""
    for button in menu.buttons:
        if button.label == label:
            menu.handle_event(click_event(button.rect.center))
            return
    raise AssertionError(f"no button labelled {label!r}")


class TestDefaultOptions:
    def test_lists_every_option_as_a_button(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        assert [b.label for b in menu.buttons] == [o.label for o in MENU_OPTIONS]

    def test_lists_the_five_expected_entries(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        assert [b.label for b in menu.buttons] == [
            "Sandbox", "Level Select", "Level Editor", "Settings", "Quit"
        ]

    def test_the_editor_is_listed_below_level_select(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)
        labels = [b.label for b in menu.buttons]

        assert labels.index("Level Editor") == labels.index("Level Select") + 1

    def test_unbuilt_options_are_listed_but_disabled(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        disabled = {b.label for b in menu.buttons if not b.enabled}
        assert disabled == {"Settings"}


class TestClickRouting:
    def test_sandbox_hands_over_to_the_sandbox_scene(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        click_label(menu, "Sandbox")

        assert isinstance(menu.next_scene, SandboxScene)
        assert menu.quit_requested is False

    def test_quit_asks_the_app_to_close(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        click_label(menu, "Quit")

        assert menu.quit_requested is True
        assert menu.next_scene is None

    def test_level_select_opens_the_level_select_screen(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        click_label(menu, "Level Select")

        assert isinstance(menu.next_scene, LevelSelectScene)
        assert menu.quit_requested is False

    def test_level_editor_opens_the_editor_screen(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        click_label(menu, "Level Editor")

        assert isinstance(menu.next_scene, LevelEditorScene)
        assert menu.quit_requested is False

    def test_disabled_options_do_nothing(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        click_label(menu, "Settings")

        assert menu.next_scene is None
        assert menu.quit_requested is False

    def test_clicking_empty_space_does_nothing(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        menu.handle_event(click_event((5, 5)))

        assert menu.next_scene is None
        assert menu.quit_requested is False

    def test_right_click_is_ignored(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)
        quit_button = next(b for b in menu.buttons if b.label == "Quit")

        menu.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": quit_button.rect.center, "button": 3}
            )
        )

        assert menu.quit_requested is False


class TestCustomOptions:
    """The point of MENU_OPTIONS being a plain list: swapping it changes the
    screen with no other edits."""

    def test_buttons_follow_a_custom_option_list(self, screen: pygame.Surface) -> None:
        options = [
            MenuOption("One", lambda menu: None),
            MenuOption("Two", lambda menu: None),
        ]

        menu = MenuScene(screen, options)

        assert [b.label for b in menu.buttons] == ["One", "Two"]

    def test_a_custom_action_runs_on_click(self, screen: pygame.Surface) -> None:
        clicked: list[str] = []
        options = [MenuOption("Press me", lambda menu: clicked.append("yes"))]
        menu = MenuScene(screen, options)

        click_label(menu, "Press me")

        assert clicked == ["yes"]

    def test_an_action_can_request_quit(self, screen: pygame.Surface) -> None:
        options = [MenuOption("Bye", lambda menu: menu.request_quit())]
        menu = MenuScene(screen, options)

        click_label(menu, "Bye")

        assert menu.quit_requested is True

    def test_an_empty_option_list_renders_nothing(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen, [])

        assert menu.buttons == []
        menu.draw()  # must not raise


class TestLayout:
    def test_buttons_stay_on_screen_and_do_not_overlap(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        for button in menu.buttons:
            assert button.rect.left >= 0
            assert button.rect.right <= screen.get_width()
            assert button.rect.top >= 0
            assert button.rect.bottom <= screen.get_height()

        for above, below in zip(menu.buttons, menu.buttons[1:]):
            assert above.rect.bottom < below.rect.top

    def test_title_sits_above_the_first_button(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)

        assert menu.title_center[1] < menu.buttons[0].rect.top

    def test_hover_tracks_the_pointer(self, screen: pygame.Surface) -> None:
        menu = MenuScene(screen)
        first = menu.buttons[0]

        menu.handle_event(motion_event(first.rect.center))
        assert first.hovered is True

        menu.handle_event(motion_event((5, 5)))
        assert first.hovered is False
