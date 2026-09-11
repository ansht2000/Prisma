"""Unit tests for LevelScene: that level 1 is a real puzzle (starts unsolved,
is solvable), that winning raises the overlay, and that the overlay's two
options behave -- including "Next Level" staying inert until a next level
actually exists.
"""
import pygame
import pytest

import levels
from level import LevelScene
from level_select import LevelSelectScene
from levels import LEVEL_ONE, LevelLayout, MirrorSpec
from mirror import Mirror

pytestmark = pytest.mark.unit

SOLVING_ANGLE = 45  # turns the mirror into a "/", steering the beam up


@pytest.fixture
def level(screen: pygame.Surface) -> LevelScene:
    return LevelScene(screen, LEVEL_ONE)


def only_mirror(scene: LevelScene) -> Mirror:
    mirror = next(iter(scene.mirrors))
    assert isinstance(mirror, Mirror)
    return mirror


def run_frame(scene: LevelScene) -> None:
    scene.update(0.016)
    scene.draw()


def click(scene: LevelScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))


def click_overlay_label(scene: LevelScene, label: str) -> None:
    assert scene.win_overlay is not None
    for button in scene.win_overlay.buttons:
        if button.label == label:
            click(scene, button.rect.center)
            return
    raise AssertionError(f"no overlay button labelled {label!r}")


class TestLevelOneIsAPuzzle:
    def test_it_does_not_start_solved(self, level: LevelScene) -> None:
        run_frame(level)

        assert level.won is False
        assert level.win_overlay is None

    def test_the_beam_misses_the_target_at_the_starting_angle(self, level: LevelScene) -> None:
        run_frame(level)

        assert level.beam is not None
        assert level.target.is_hit_by(level.beam.beam_path) is False

    def test_rotating_the_mirror_to_45_wins(self, level: LevelScene) -> None:
        run_frame(level)

        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        assert level.won is True

    def test_the_beam_reaches_the_target_once_solved(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        assert level.beam is not None
        assert level.target.is_hit_by(level.beam.beam_path) is True

    def test_the_beam_bounces_rather_than_going_straight(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        assert level.beam is not None
        # start -> mirror -> onwards, so at least one reflection point
        assert len(level.beam.beam_path) >= 3

    def test_winning_is_sticky(self, level: LevelScene) -> None:
        """Turning the mirror away again should not un-win a finished level."""
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        only_mirror(level).set_orientation(90)
        run_frame(level)

        assert level.won is True


class TestWinOverlay:
    def test_it_appears_with_both_options(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        assert level.win_overlay is not None
        assert [b.label for b in level.win_overlay.buttons] == ["Level Select", "Next Level"]

    def test_next_level_is_disabled_while_level_one_is_the_last(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        assert level.win_overlay is not None
        by_label = {b.label: b for b in level.win_overlay.buttons}
        assert by_label["Level Select"].enabled is True
        assert by_label["Next Level"].enabled is False

    def test_level_select_goes_back_to_the_level_select_screen(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        click_overlay_label(level, "Level Select")

        assert isinstance(level.next_scene, LevelSelectScene)

    def test_next_level_does_nothing_for_now(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)

        click_overlay_label(level, "Next Level")

        assert level.next_scene is None

    def test_next_level_works_once_another_level_exists(
        self, screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The payoff of the registry: adding a level makes this button live
        without touching LevelScene."""
        second = LevelLayout(
            number=2,
            hint="",
            laser_cell=(0, 2),
            laser_orientation=0,
            target_cell=(4, 0),
            mirrors=(MirrorSpec(cell=(4, 2), orientation=90),),
        )
        monkeypatch.setattr(levels, "LEVELS", [LEVEL_ONE, second])
        scene = LevelScene(screen, LEVEL_ONE)

        only_mirror(scene).set_orientation(SOLVING_ANGLE)
        run_frame(scene)

        assert scene.win_overlay is not None
        by_label = {b.label: b for b in scene.win_overlay.buttons}
        assert by_label["Next Level"].enabled is True

        click_overlay_label(scene, "Next Level")

        assert isinstance(scene.next_scene, LevelScene)
        assert scene.next_scene.layout.number == 2

    def test_the_overlay_swallows_clicks_meant_for_the_board(self, level: LevelScene) -> None:
        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level)
        mirror = only_mirror(level)
        assert mirror.rect is not None

        click(level, mirror.rect.center)

        assert level.input_box is None


class TestControls:
    def test_clicking_a_mirror_opens_the_degree_box(self, level: LevelScene) -> None:
        run_frame(level)
        mirror = only_mirror(level)
        assert mirror.rect is not None

        click(level, mirror.rect.center)

        assert level.input_box is not None

    def test_clicking_empty_board_opens_nothing(self, level: LevelScene) -> None:
        run_frame(level)

        click(level, (5, 5))

        assert level.input_box is None

    def test_typing_an_angle_can_solve_the_level(self, level: LevelScene) -> None:
        run_frame(level)
        mirror = only_mirror(level)
        assert mirror.rect is not None
        click(level, mirror.rect.center)

        for char in str(SOLVING_ANGLE):
            level.handle_event(
                pygame.event.Event(pygame.KEYDOWN, {"key": ord(char), "unicode": char})
            )
        level.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": "\r"}))
        run_frame(level)

        assert level.input_box is None
        assert level.won is True

    def test_escape_backs_out_to_level_select(self, level: LevelScene) -> None:
        run_frame(level)

        level.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

        assert isinstance(level.next_scene, LevelSelectScene)

    def test_escape_cancels_the_degree_box_before_leaving(self, level: LevelScene) -> None:
        run_frame(level)
        mirror = only_mirror(level)
        assert mirror.rect is not None
        click(level, mirror.rect.center)

        level.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""}))

        assert level.input_box is None
        assert level.next_scene is None  # still in the level


class TestBoard:
    def test_pieces_sit_on_their_cells(self, level: LevelScene) -> None:
        assert (level.laser.pos_x, level.laser.pos_y) == level.cell_center(*LEVEL_ONE.laser_cell)
        assert level.target.rect.center == tuple(
            int(v) for v in level.cell_center(*LEVEL_ONE.target_cell)
        )

    def test_pieces_stay_out_of_the_sandbox_sprite_groups(self, level: LevelScene) -> None:
        """Level pieces are built with add_to_groups=False, so they never join
        whatever groups the sandbox last configured."""
        assert level.laser.groups() == []
        assert level.beam is None or level.beam.groups() == []
