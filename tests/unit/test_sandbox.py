"""Unit tests for SandboxScene: dragging each kind of piece off the table,
deleting it again, and what a beam does when it meets a wall.

tests/integration/test_click_to_snap.py drives the same scene through the real
app loop; these poke it directly, so they can look at what it is holding.
"""
import pygame
import pytest

from laser import Laser
from laserbeam import LaserBeam
from menu import MenuScene
from mirror import Mirror
from sandbox import NEW_PIECES, SandboxScene
from wall import Wall

pytestmark = pytest.mark.unit


@pytest.fixture
def sandbox(screen: pygame.Surface) -> SandboxScene:
    """A sandbox that has drawn once, so its table knows where its entries are."""
    scene = SandboxScene(screen)
    scene.draw()
    return scene


def press(scene: SandboxScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))


def release(scene: SandboxScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1}))


def right_click(scene: SandboxScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 3}))


def drag_out(scene: SandboxScene, kind: str, to: tuple[float, float]) -> None:
    """Drags a piece off the table and drops it at `to`.

    update() is what normally walks a held piece to the pointer, and the dummy
    video driver pins that at the origin, so the move is made directly here.
    """
    press(scene, scene.table.entry_rects[kind].center)
    assert scene.selected is not None
    scene.selected.set_position(*to)
    release(scene, to)


class TestDraggingPiecesOut:
    @pytest.mark.parametrize("kind", ["mirror", "laser", "wall"])
    def test_each_kind_can_be_dragged_out(self, sandbox: SandboxScene, kind: str) -> None:
        drag_out(sandbox, kind, (400, 300))

        assert len(sandbox.pieces()) == 1

    def test_a_wall_lands_in_the_wall_group(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "wall", (400, 300))

        assert len(sandbox.walls) == 1
        assert isinstance(next(iter(sandbox.walls)), Wall)

    def test_a_new_wall_is_drawn_and_can_be_deleted(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "wall", (400, 300))

        wall = next(iter(sandbox.walls))
        assert wall in sandbox.drawable
        assert wall in sandbox.deletable

    def test_pressing_the_table_picks_a_piece_up_before_it_is_dropped(
        self, sandbox: SandboxScene
    ) -> None:
        press(sandbox, sandbox.table.entry_rects["wall"].center)

        assert sandbox.dragging is True
        assert isinstance(sandbox.selected, Wall)

    def test_the_table_offers_the_three_things_free_play_can_use(
        self, sandbox: SandboxScene
    ) -> None:
        assert set(NEW_PIECES) == {"mirror", "laser", "wall"}
        for kind in NEW_PIECES:
            assert kind in sandbox.table.entry_rects


class TestPickingPiecesUpAgain:
    def test_a_placed_wall_can_be_picked_back_up(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "wall", (400, 300))
        sandbox.draw()
        wall = next(iter(sandbox.walls))
        assert wall.rect is not None

        press(sandbox, wall.rect.center)

        assert sandbox.selected is wall
        assert sandbox.click_target is wall

    def test_clicking_a_wall_opens_the_degree_box(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "wall", (400, 300))
        sandbox.draw()
        wall = next(iter(sandbox.walls))
        assert wall.rect is not None
        spot = wall.rect.center

        press(sandbox, spot)
        release(sandbox, spot)

        assert sandbox.input_box is not None

    def test_typing_an_angle_turns_the_wall(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "wall", (400, 300))
        sandbox.draw()
        wall = next(iter(sandbox.walls))
        assert wall.rect is not None
        spot = wall.rect.center
        press(sandbox, spot)
        release(sandbox, spot)

        for char in "30":
            sandbox.handle_event(
                pygame.event.Event(pygame.KEYDOWN, {"key": ord(char), "unicode": char})
            )
        sandbox.handle_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": "\r"})
        )

        assert sandbox.input_box is None
        assert wall.orientation == 30


class TestWallsBlockBeams:
    def test_a_beam_stops_at_a_wall(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "laser", (200, 300))
        drag_out(sandbox, "wall", (500, 300))
        sandbox.draw()
        laser = next(iter(sandbox.lasers))
        assert laser.rect is not None

        right_click(sandbox, laser.rect.center)

        assert laser.laser_beam is not None
        assert laser.laser_beam.beam_path[-1].x == pytest.approx(500, abs=2)

    def test_the_beam_is_told_about_the_walls(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "laser", (200, 300))
        sandbox.draw()
        laser = next(iter(sandbox.lasers))
        assert laser.rect is not None

        right_click(sandbox, laser.rect.center)

        assert laser.laser_beam is not None
        assert laser.laser_beam.walls is sandbox.walls

    def test_without_a_wall_the_beam_runs_to_the_table(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "laser", (200, 300))
        sandbox.draw()
        laser = next(iter(sandbox.lasers))
        assert laser.rect is not None

        right_click(sandbox, laser.rect.center)

        assert laser.laser_beam is not None
        assert laser.laser_beam.beam_path[-1].x == pytest.approx(sandbox.table.width, abs=2)


class TestNavigation:
    def test_escape_backs_out_to_the_menu(self, sandbox: SandboxScene) -> None:
        sandbox.handle_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""})
        )

        assert isinstance(sandbox.next_scene, MenuScene)

    def test_the_degree_box_swallows_escape_first(self, sandbox: SandboxScene) -> None:
        drag_out(sandbox, "mirror", (400, 300))
        sandbox.draw()
        mirror = next(iter(sandbox.mirrors))
        assert mirror.rect is not None
        press(sandbox, mirror.rect.center)
        release(sandbox, mirror.rect.center)

        sandbox.handle_event(
            pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""})
        )

        assert sandbox.input_box is None
        assert sandbox.next_scene is None

    def test_drawing_a_full_screen_of_pieces_does_not_raise(
        self, sandbox: SandboxScene
    ) -> None:
        for index, kind in enumerate(["mirror", "laser", "wall"] * 3):
            drag_out(sandbox, kind, (150 + index * 60, 200))

        sandbox.draw()

        assert len(sandbox.pieces()) == 9


def test_every_piece_kind_reaches_its_own_group(screen: pygame.Surface) -> None:
    scene = SandboxScene(screen)

    assert isinstance(_made(scene, "mirror"), Mirror)
    assert isinstance(_made(scene, "laser"), Laser)
    assert isinstance(_made(scene, "wall"), Wall)


def _made(scene: SandboxScene, kind: str) -> object:
    return NEW_PIECES[kind](0, 0, scene.screen)
