"""Unit tests for LevelSelectScene: one box per registered level, anchored to
the top-right corner, and clicking one starts that level.
"""
import pygame
import pytest

from level import LevelScene
from level_select import LevelSelectScene
from levels import LEVELS, LevelLayout, MirrorSpec
from menu import MenuScene

pytestmark = pytest.mark.unit


def make_layout(number: int) -> LevelLayout:
    return LevelLayout(
        number=number,
        hint="",
        laser_cell=(0, 2),
        laser_orientation=0,
        target_cell=(4, 0),
        mirrors=(MirrorSpec(cell=(4, 2), orientation=90),),
    )


def click(scene: LevelSelectScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))


class TestBoxes:
    def test_one_box_per_registered_level(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        assert [b.label for b in scene.buttons] == [str(l.number) for l in LEVELS]

    def test_the_only_box_is_level_one(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        assert [b.label for b in scene.buttons] == ["1"]

    def test_level_one_sits_in_the_top_left_corner(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)
        box = scene.buttons[0]

        # Nearer the top than the bottom, and nearer the left than the right
        assert box.rect.top < screen.get_height() - box.rect.bottom
        assert box.rect.left < screen.get_width() - box.rect.right

    def test_boxes_start_below_the_heading(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        title_bottom = scene.title_center[1] + scene.title_font.get_height() // 2
        for box in scene.buttons:
            assert box.rect.top >= title_bottom

    def test_the_heading_sits_at_the_top_of_the_screen(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        assert scene.title_center[1] < screen.get_height() // 4

    def test_boxes_are_square(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        for box in scene.buttons:
            assert box.rect.width == box.rect.height

    def test_boxes_follow_a_custom_level_list(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen, [make_layout(1), make_layout(2), make_layout(3)])

        assert [b.label for b in scene.buttons] == ["1", "2", "3"]

    def test_extra_levels_fill_rightwards_from_the_corner(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen, [make_layout(1), make_layout(2)])

        first, second = scene.buttons
        assert first.rect.right < second.rect.left
        assert first.rect.top == second.rect.top

    def test_boxes_stay_on_screen(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen, [make_layout(n) for n in range(1, 13)])

        for box in scene.buttons:
            assert box.rect.left >= 0
            assert box.rect.right <= screen.get_width()
            assert box.rect.top >= 0
            assert box.rect.bottom <= screen.get_height()


class TestNavigation:
    def test_clicking_a_box_starts_that_level(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        click(scene, scene.buttons[0].rect.center)

        assert isinstance(scene.next_scene, LevelScene)
        assert scene.next_scene.layout.number == 1

    def test_clicking_empty_space_does_nothing(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        click(scene, (screen.get_width() // 2, screen.get_height() // 2))

        assert scene.next_scene is None

    def test_escape_backs_out_to_the_menu(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

        assert isinstance(scene.next_scene, MenuScene)

    def test_hover_tracks_the_pointer(self, screen: pygame.Surface) -> None:
        scene = LevelSelectScene(screen)
        box = scene.buttons[0]

        scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": box.rect.center}))
        assert box.hovered is True

        scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5)}))
        assert box.hovered is False
