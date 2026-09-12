"""Unit tests for CustomLevelSelectScene: listing what the editor saved,
starting one, and coming back to the right screen afterwards.
"""
from pathlib import Path

import pygame
import pytest

from custom_level_select import CustomLevelSelectScene
from custom_levels import CustomLevel, save
from level import LevelScene
from levels import MirrorSpec
from menu import MenuScene

pytestmark = pytest.mark.unit


def playable(name: str, target: tuple[int, int] = (4, 0)) -> CustomLevel:
    return CustomLevel(
        name=name,
        laser_cell=(0, 2),
        laser_orientation=0.0,
        target_cell=target,
        mirrors=(MirrorSpec(cell=(4, 2), orientation=90.0),),
    )


def click(scene: CustomLevelSelectScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))


class TestListing:
    def test_one_box_per_saved_level(self, screen: pygame.Surface, tmp_path: Path) -> None:
        save(playable("one"), tmp_path)
        save(playable("two"), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert len(scene.buttons) == 2

    def test_boxes_are_labelled_with_the_level_name(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("Tricky bounce"), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert scene.buttons[0].label == "Tricky bounce"

    def test_levels_are_listed_in_name_order(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        for name in ("zigzag", "Apple", "middle"):
            save(playable(name), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert [b.label for b in scene.buttons] == ["Apple", "middle", "zigzag"]

    def test_a_long_name_is_shortened_to_fit_its_box(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("an extremely long level name"), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        label = scene.buttons[0].label
        assert label.endswith("...")
        assert scene.box_font.size(label)[0] <= scene.buttons[0].rect.width

    def test_a_missing_directory_lists_nothing(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        scene = CustomLevelSelectScene(screen, directory=tmp_path / "not_created_yet")

        assert scene.buttons == []
        scene.draw()  # the empty screen must still draw

    def test_a_level_that_cannot_be_played_is_listed_but_disabled(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        # No laser, so there is nothing to aim at the target
        save(CustomLevel(name="half finished", target_cell=(4, 0)), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert [b.label for b in scene.buttons] == ["half finished"]
        assert scene.buttons[0].enabled is False

    def test_a_level_with_nothing_to_move_is_listed_but_disabled(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        # A laser aimed straight at the target with no mirrors in between is
        # not a puzzle -- it would be won the moment it opened
        save(
            CustomLevel(name="no mirrors", laser_cell=(0, 2), target_cell=(4, 2)),
            tmp_path,
        )

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert [b.label for b in scene.buttons] == ["no mirrors"]
        assert scene.buttons[0].enabled is False

    def test_an_unreadable_file_is_left_out(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("good"), tmp_path)
        (tmp_path / "broken.toml").write_text("this is not = valid = toml")

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert [b.label for b in scene.buttons] == ["good"]


class TestLayout:
    def test_boxes_start_below_the_heading(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("one"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        title_bottom = scene.title_center[1] + scene.title_font.get_height() // 2
        assert scene.buttons[0].rect.top >= title_bottom

    def test_the_first_box_is_at_the_left_margin(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("one"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        assert scene.buttons[0].rect.left < screen.get_width() // 4

    def test_extra_levels_fill_rightwards_then_wrap(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        for index in range(12):
            save(playable(f"level{index:02d}"), tmp_path)

        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        first, second = scene.buttons[0], scene.buttons[1]
        assert first.rect.right < second.rect.left
        assert first.rect.top == second.rect.top
        # and they stay on screen once they have to wrap
        for box in scene.buttons:
            assert box.rect.right <= screen.get_width()
            assert box.rect.bottom <= screen.get_height()


class TestPlaying:
    def test_clicking_a_box_starts_that_level(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("bounce"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        click(scene, scene.buttons[0].rect.center)

        assert isinstance(scene.next_scene, LevelScene)
        assert scene.next_scene.layout.laser_cell == (0, 2)

    def test_clicking_an_unplayable_level_does_nothing(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(CustomLevel(name="half finished", target_cell=(4, 0)), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        click(scene, scene.buttons[0].rect.center)

        assert scene.next_scene is None

    def test_leaving_a_custom_level_comes_back_to_this_screen(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("bounce", target=(7, 5)), tmp_path)  # not solved on the first frame
        scene = CustomLevelSelectScene(screen, directory=tmp_path)
        click(scene, scene.buttons[0].rect.center)
        level = scene.next_scene
        assert isinstance(level, LevelScene)

        level.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

        assert isinstance(level.next_scene, CustomLevelSelectScene)

    def test_next_level_walks_the_custom_levels(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("a first"), tmp_path)
        save(playable("b second"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)
        click(scene, scene.buttons[0].rect.center)
        level = scene.next_scene
        assert isinstance(level, LevelScene)

        level.go_to_next_level()

        assert isinstance(level.next_scene, LevelScene)
        assert level.next_scene.layout.hint == "b second"

    def test_the_last_custom_level_has_nothing_after_it(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("only one"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)
        click(scene, scene.buttons[0].rect.center)
        level = scene.next_scene
        assert isinstance(level, LevelScene)

        level.go_to_next_level()

        assert level.next_scene is None

    def test_a_custom_level_never_leads_into_the_built_in_ones(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        save(playable("only one"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)
        click(scene, scene.buttons[0].rect.center)
        level = scene.next_scene
        assert isinstance(level, LevelScene)

        assert level.playlist is scene.playlist


class TestNavigation:
    def test_escape_backs_out_to_the_menu(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        scene = CustomLevelSelectScene(screen, directory=tmp_path)

        scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

        assert isinstance(scene.next_scene, MenuScene)

    def test_hover_tracks_the_pointer(self, screen: pygame.Surface, tmp_path: Path) -> None:
        save(playable("one"), tmp_path)
        scene = CustomLevelSelectScene(screen, directory=tmp_path)
        box = scene.buttons[0]

        scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": box.rect.center}))
        assert box.hovered is True

        scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 700)}))
        assert box.hovered is False
