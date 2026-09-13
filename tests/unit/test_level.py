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
from constants import LEVEL_UNTOUCHED_HINT, TARGET_CHARGE_SECONDS
from levels import LEVEL_ONE, LevelLayout, MirrorSpec, WallSpec
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


def run_frame(scene: LevelScene, dt: float = 0.016) -> None:
    scene.update(dt)
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


class TestCannotBeWonInstantly:
    """A level whose beam already lands on the target before anything has been
    touched -- easy to build in the editor -- must not hand out the win on its
    first frame."""

    def pre_solved(self) -> LevelLayout:
        # Level one, except the mirror already sits at the solving angle
        return LevelLayout(
            number=1,
            hint="",
            laser_cell=(0, 2),
            laser_orientation=0,
            target_cell=(4, 0),
            mirrors=(MirrorSpec(cell=(4, 2), orientation=SOLVING_ANGLE),),
        )

    def test_the_beam_is_on_the_target_from_the_first_frame(
        self, screen: pygame.Surface
    ) -> None:
        scene = LevelScene(screen, self.pre_solved())

        run_frame(scene)

        assert scene.beam is not None
        assert scene.target.is_hit_by(scene.beam.beam_path) is True

    def test_it_is_not_won_before_anything_is_moved(self, screen: pygame.Surface) -> None:
        scene = LevelScene(screen, self.pre_solved())

        for _ in range(5):
            run_frame(scene)

        assert scene.won is False
        assert scene.win_overlay is None

    def test_moving_a_mirror_off_target_does_not_win_either(
        self, screen: pygame.Surface
    ) -> None:
        scene = LevelScene(screen, self.pre_solved())
        run_frame(scene)

        only_mirror(scene).set_orientation(90)
        run_frame(scene)

        assert scene.won is False

    def test_it_can_still_be_won_by_playing_it(self, screen: pygame.Surface) -> None:
        scene = LevelScene(screen, self.pre_solved())
        run_frame(scene)

        only_mirror(scene).set_orientation(90)
        run_frame(scene)
        only_mirror(scene).set_orientation(SOLVING_ANGLE)
        run_frame(scene)

        assert scene.won is True

    def test_having_touched_it_sticks(self, screen: pygame.Surface) -> None:
        """Turning a mirror back to where it started still counts as played."""
        scene = LevelScene(screen, self.pre_solved())
        run_frame(scene)

        only_mirror(scene).set_orientation(SOLVING_ANGLE + 10)
        run_frame(scene)
        only_mirror(scene).set_orientation(SOLVING_ANGLE)
        run_frame(scene)

        assert scene.touched is True
        assert scene.won is True

    def test_level_one_counts_as_untouched_to_begin_with(self, level: LevelScene) -> None:
        assert level.touched is False

    def test_it_asks_the_player_to_move_something(self, screen: pygame.Surface) -> None:
        """Otherwise the board just sits there looking solved and silent."""
        scene = LevelScene(screen, self.pre_solved())

        run_frame(scene)

        assert scene.footer_text == LEVEL_UNTOUCHED_HINT

    def test_the_prompt_goes_away_once_it_is_played(self, screen: pygame.Surface) -> None:
        scene = LevelScene(screen, self.pre_solved())
        run_frame(scene)

        only_mirror(scene).set_orientation(90)
        run_frame(scene)

        assert scene.footer_text == scene.layout.hint

    def test_an_ordinary_level_shows_its_own_hint(self, level: LevelScene) -> None:
        run_frame(level)

        assert level.footer_text == LEVEL_ONE.hint

    def test_a_level_with_nothing_to_move_is_not_held_back(
        self, screen: pygame.Surface
    ) -> None:
        """There is no move to wait for, so the gate does not apply -- such a
        level is kept off the custom list instead (see custom_levels.to_layout)."""
        no_mirrors = LevelLayout(
            number=1,
            hint="",
            laser_cell=(0, 2),
            laser_orientation=0,
            target_cell=(4, 0),
            mirrors=(),
        )

        scene = LevelScene(screen, no_mirrors)

        assert scene.touched is True


class TestHoldingTheBeamOnTheTarget:
    """Crossing the target is not enough: the beam has to stay on it while the
    target fills, and only a full target wins.

    The one place the charge time matters, so it is the one place that puts
    the real duration back (see tests/conftest.py).
    """

    @pytest.fixture(autouse=True)
    def use_the_real_charge_time(self, real_target_charge: float) -> None:
        pass

    def solve(self, level: LevelScene) -> None:
        run_frame(level)
        only_mirror(level).set_orientation(SOLVING_ANGLE)

    def test_landing_the_beam_does_not_win_on_its_own(self, level: LevelScene) -> None:
        self.solve(level)

        run_frame(level)

        assert level.beam is not None
        assert level.target.is_hit_by(level.beam.beam_path) is True
        assert level.won is False

    def test_the_target_starts_filling(self, level: LevelScene) -> None:
        self.solve(level)

        run_frame(level, TARGET_CHARGE_SECONDS / 2)

        assert level.target.charge == pytest.approx(0.5)
        assert level.won is False

    def test_it_is_still_not_won_just_short_of_the_time(self, level: LevelScene) -> None:
        self.solve(level)

        run_frame(level, TARGET_CHARGE_SECONDS - 0.1)

        assert level.won is False

    def test_it_is_won_once_the_target_is_full(self, level: LevelScene) -> None:
        self.solve(level)

        run_frame(level, TARGET_CHARGE_SECONDS)

        assert level.target.is_charged is True
        assert level.won is True

    def test_taking_the_beam_away_starts_it_draining(self, level: LevelScene) -> None:
        self.solve(level)
        run_frame(level, TARGET_CHARGE_SECONDS / 2)

        only_mirror(level).set_orientation(90)  # beam swings off the target
        run_frame(level, TARGET_CHARGE_SECONDS / 4)

        assert level.target.charge == pytest.approx(0.25)
        assert level.won is False

    def test_it_drains_all_the_way_if_the_beam_stays_away(
        self, level: LevelScene
    ) -> None:
        self.solve(level)
        run_frame(level, TARGET_CHARGE_SECONDS / 2)

        only_mirror(level).set_orientation(90)
        run_frame(level, TARGET_CHARGE_SECONDS)

        assert level.target.charge == 0

    def test_bringing_the_beam_back_makes_up_only_what_was_lost(
        self, level: LevelScene
    ) -> None:
        self.solve(level)
        run_frame(level, TARGET_CHARGE_SECONDS * 0.75)
        only_mirror(level).set_orientation(90)
        run_frame(level, TARGET_CHARGE_SECONDS / 4)

        only_mirror(level).set_orientation(SOLVING_ANGLE)
        run_frame(level, TARGET_CHARGE_SECONDS / 2)

        assert level.won is True

    def test_an_unsolved_level_never_starts_filling(self, level: LevelScene) -> None:
        run_frame(level, TARGET_CHARGE_SECONDS * 3)

        assert level.target.charge == 0

    def test_the_target_stays_full_once_the_level_is_won(self, level: LevelScene) -> None:
        self.solve(level)
        run_frame(level, TARGET_CHARGE_SECONDS)
        assert level.won is True

        only_mirror(level).set_orientation(90)  # beam swings off it again
        run_frame(level, TARGET_CHARGE_SECONDS)

        assert level.target.is_charged is True

    def test_a_pre_solved_level_does_not_fill_until_it_is_played(
        self, screen: pygame.Surface
    ) -> None:
        # The beam is on the target from the first frame, but nothing has been
        # moved, so there is nothing to charge yet (see TestCannotBeWonInstantly)
        scene = LevelScene(screen, TestCannotBeWonInstantly().pre_solved())

        run_frame(scene, TARGET_CHARGE_SECONDS * 2)

        assert scene.target.charge == 0
        assert scene.won is False


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


class TestWalls:
    """A level can hold walls, which the beam stops at."""

    def walled(self, walls: tuple[WallSpec, ...]) -> LevelLayout:
        # Laser fires right along row 2 at a target on the far side of it
        return LevelLayout(
            number=1,
            hint="",
            laser_cell=(0, 2),
            laser_orientation=0,
            target_cell=(7, 2),
            mirrors=(MirrorSpec(cell=(4, 4), orientation=90),),
            walls=walls,
        )

    def test_a_level_without_walls_has_none(self, level: LevelScene) -> None:
        assert list(level.walls) == []

    def test_a_wall_in_the_way_keeps_the_beam_off_the_target(
        self, screen: pygame.Surface
    ) -> None:
        scene = LevelScene(screen, self.walled((WallSpec(cell=(4, 2), orientation=90),)))

        run_frame(scene)

        assert scene.beam is not None
        assert scene.target.is_hit_by(scene.beam.beam_path) is False
        assert scene.won is False

    def test_the_same_level_without_the_wall_is_a_straight_shot(
        self, screen: pygame.Surface
    ) -> None:
        scene = LevelScene(screen, self.walled(()))

        run_frame(scene)

        assert scene.beam is not None
        assert scene.target.is_hit_by(scene.beam.beam_path) is True

    def test_the_beam_ends_at_the_wall(self, screen: pygame.Surface) -> None:
        scene = LevelScene(screen, self.walled((WallSpec(cell=(4, 2), orientation=90),)))

        run_frame(scene)

        assert scene.beam is not None
        wall_x, _ = scene.cell_center(4, 2)
        assert scene.beam.beam_path[-1].x == pytest.approx(wall_x)

    def test_every_wall_in_the_layout_is_built(self, screen: pygame.Surface) -> None:
        walls = (
            WallSpec(cell=(2, 2), orientation=90),
            WallSpec(cell=(5, 1), orientation=0),
        )

        scene = LevelScene(screen, self.walled(walls))

        assert len(scene.walls) == 2

    def test_the_beam_is_told_about_the_walls(self, screen: pygame.Surface) -> None:
        scene = LevelScene(screen, self.walled((WallSpec(cell=(4, 2), orientation=90),)))

        run_frame(scene)

        assert scene.beam is not None
        assert scene.beam.walls is scene.walls

    def test_walls_do_not_turn_when_the_player_rotates_a_mirror(
        self, screen: pygame.Surface
    ) -> None:
        """Only mirrors are the player's to move."""
        scene = LevelScene(screen, self.walled((WallSpec(cell=(4, 2), orientation=90),)))
        run_frame(scene)
        wall = next(iter(scene.walls))

        click(scene, (wall.rect.centerx, wall.rect.centery))

        assert scene.input_box is None


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
