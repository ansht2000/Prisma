"""Unit tests for Wall: the same line a mirror is, drawn thicker and grey."""
import pygame
import pytest

from constants import MIRROR_WIDTH, WALL_COLOR, WALL_WIDTH
from mirror import Mirror
from wall import Wall

pytestmark = pytest.mark.unit


class TestGeometry:
    def test_it_stands_upright_by_default(self, screen: pygame.Surface) -> None:
        # So a wall dropped in front of a laser blocks it instead of lying
        # along the beam
        assert Wall(100, 100, screen).orientation == 90

    def test_drawing_gives_it_its_ends(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60, orientation=90)

        wall.draw()

        assert wall.start_pos is not None and wall.end_pos is not None
        assert (wall.start_pos - wall.end_pos).length() == pytest.approx(60)

    def test_an_upright_wall_runs_vertically(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60, orientation=90)

        wall.draw()

        assert wall.start_pos is not None and wall.end_pos is not None
        assert wall.start_pos.x == pytest.approx(wall.end_pos.x)

    def test_a_flat_wall_runs_horizontally(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60, orientation=0)

        wall.draw()

        assert wall.start_pos is not None and wall.end_pos is not None
        assert wall.start_pos.y == pytest.approx(wall.end_pos.y)

    def test_it_is_centered_on_its_position(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60, orientation=90)

        wall.draw()

        assert wall.rect is not None
        assert wall.rect.center == pytest.approx((100, 200), abs=1)

    def test_moving_it_moves_what_it_draws(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60)
        wall.draw()

        wall.set_position(300, 400)
        wall.draw()

        assert wall.rect is not None
        assert wall.rect.center == pytest.approx((300, 400), abs=1)

    def test_turning_it_wraps_around(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen)

        wall.set_orientation(450)

        assert wall.orientation == 90


class TestAppearance:
    def test_it_is_thicker_than_a_mirror(self) -> None:
        assert WALL_WIDTH > MIRROR_WIDTH

    def test_it_is_grey(self) -> None:
        red, green, blue = WALL_COLOR
        assert red == green == blue
        assert 0 < red < 255  # neither black nor white

    def test_it_is_drawn_in_that_grey(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        wall = Wall(100, 200, screen, length=60, orientation=90)

        wall.draw()

        assert screen.get_at((100, 200))[:3] == WALL_COLOR

    def test_its_hitbox_covers_its_thickness(self, screen: pygame.Surface) -> None:
        wall = Wall(100, 200, screen, length=60, orientation=90)

        wall.draw()

        assert wall.rect is not None
        assert wall.rect.width >= WALL_WIDTH


class TestSpriteGroups:
    def test_a_wall_joins_the_sandbox_groups_like_any_other_piece(
        self, screen: pygame.Surface
    ) -> None:
        walls: pygame.sprite.Group = pygame.sprite.Group()
        Wall.containers = (walls,)
        try:
            assert Wall(0, 0, screen).groups() == [walls]
        finally:
            del Wall.containers

    def test_a_wall_can_be_kept_out_of_them(self, screen: pygame.Surface) -> None:
        """Levels and the editor build their own walls, and must not land in
        whatever groups the sandbox last set up."""
        walls: pygame.sprite.Group = pygame.sprite.Group()
        Wall.containers = (walls,)
        try:
            assert Wall(0, 0, screen, add_to_groups=False).groups() == []
        finally:
            del Wall.containers

    def test_it_can_still_be_put_in_a_group_by_hand(self, screen: pygame.Surface) -> None:
        walls: pygame.sprite.Group = pygame.sprite.Group()

        wall = Wall(0, 0, screen, add_to_groups=False)
        walls.add(wall)

        assert list(walls) == [wall]


def test_a_wall_is_not_a_mirror(screen: pygame.Surface) -> None:
    # laserbeam.py tells them apart with isinstance, so this has to hold
    assert not isinstance(Wall(0, 0, screen), Mirror)
