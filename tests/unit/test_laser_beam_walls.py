"""Unit tests for what the beam does when it runs into a wall: it stops there,
rather than bouncing off it or carrying on through it.
"""
import pygame
import pytest

from laserbeam import LaserBeam
from mirror import Mirror
from wall import Wall

pytestmark = pytest.mark.unit

START = pygame.Vector2(100, 300)  # beam fires from here, to the right
FACING_RIGHT = 0


def group(*pieces: Mirror | Wall) -> pygame.sprite.Group:
    made: pygame.sprite.Group = pygame.sprite.Group()
    for piece in pieces:
        piece.draw()  # a piece has no ends to intersect until it is drawn
        made.add(piece)
    return made


def beam(
    screen: pygame.Surface,
    mirrors: pygame.sprite.Group | None = None,
    walls: pygame.sprite.Group | None = None,
) -> LaserBeam:
    return LaserBeam(
        pygame.Vector2(START),
        screen,
        FACING_RIGHT,
        pygame.sprite.Group() if mirrors is None else mirrors,
        add_to_groups=False,
        right_boundary=screen.get_width(),
        walls=walls,
    )


def upright_wall(screen: pygame.Surface, x: float) -> Wall:
    return Wall(x, START.y, screen, length=120, orientation=90)


def slanted_mirror(screen: pygame.Surface, x: float) -> Mirror:
    return Mirror(x, START.y, screen, length=120, orientation=45)


class TestStopping:
    def test_the_beam_ends_at_the_wall(self, screen: pygame.Surface) -> None:
        path = beam(screen, walls=group(upright_wall(screen, 400))).beam_path

        assert path[-1].x == pytest.approx(400)
        assert path[-1].y == pytest.approx(START.y)

    def test_nothing_is_drawn_past_the_wall(self, screen: pygame.Surface) -> None:
        path = beam(screen, walls=group(upright_wall(screen, 400))).beam_path

        # Start, then the wall, and that is the whole beam
        assert len(path) == 2
        assert max(point.x for point in path) == pytest.approx(400)

    def test_without_the_wall_it_would_have_carried_on(self, screen: pygame.Surface) -> None:
        path = beam(screen).beam_path

        assert path[-1].x > 400

    def test_a_wall_does_not_reflect_the_beam(self, screen: pygame.Surface) -> None:
        # A wall at 45 degrees would send the beam upwards if it behaved like
        # a mirror; it must simply stop it instead
        slanted = Wall(400, START.y, screen, length=120, orientation=45)

        path = beam(screen, walls=group(slanted)).beam_path

        assert len(path) == 2
        assert path[-1].y == pytest.approx(START.y)

    def test_a_wall_out_of_the_way_changes_nothing(self, screen: pygame.Surface) -> None:
        aside = Wall(400, START.y + 300, screen, length=120, orientation=90)

        path = beam(screen, walls=group(aside)).beam_path

        assert path[-1].x == pytest.approx(screen.get_width())


class TestWallsAndMirrorsTogether:
    def test_a_wall_in_front_of_a_mirror_stops_the_beam_first(
        self, screen: pygame.Surface
    ) -> None:
        path = beam(
            screen,
            mirrors=group(slanted_mirror(screen, 600)),
            walls=group(upright_wall(screen, 400)),
        ).beam_path

        assert len(path) == 2
        assert path[-1].x == pytest.approx(400)

    def test_a_mirror_in_front_of_a_wall_bounces_the_beam_away(
        self, screen: pygame.Surface
    ) -> None:
        path = beam(
            screen,
            mirrors=group(slanted_mirror(screen, 400)),
            walls=group(upright_wall(screen, 600)),
        ).beam_path

        # Bounced upwards at the mirror, so the wall beyond it is never reached
        assert len(path) == 3
        assert path[1].x == pytest.approx(400)
        assert path[2].y < START.y

    def test_a_bounced_beam_can_still_be_stopped_by_a_wall(
        self, screen: pygame.Surface
    ) -> None:
        # Bounced straight up at x=400, into a wall lying across that column
        above = Wall(400, START.y - 200, screen, length=200, orientation=0)

        path = beam(
            screen,
            mirrors=group(slanted_mirror(screen, 400)),
            walls=group(above),
        ).beam_path

        assert len(path) == 3
        assert path[2].x == pytest.approx(400)
        assert path[2].y == pytest.approx(START.y - 200)


def test_a_beam_with_no_walls_at_all_still_works(screen: pygame.Surface) -> None:
    # The sandbox never passes any, so the argument has to stay optional
    plain = LaserBeam(
        pygame.Vector2(START), screen, FACING_RIGHT, pygame.sprite.Group(), add_to_groups=False
    )

    assert len(plain.beam_path) == 2
    assert list(plain.walls) == []
