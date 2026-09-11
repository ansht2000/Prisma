"""Unit tests for the LaserBeam following a laser through set_orientation().

These guard the fix that motivated splitting Laser.draw() into
_compute_corners() + draw(): a snap must recompute the emitter point before
repositioning the beam, not leave it stale until the next frame.
"""
import pygame
import pytest

from laser import Laser
from laserbeam import LaserBeam

pytestmark = pytest.mark.unit


@pytest.fixture
def lit_laser(screen: pygame.Surface) -> Laser:
    laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
    laser.draw()
    mirrors: pygame.sprite.Group = pygame.sprite.Group()  # empty: beam travels unobstructed
    laser.laser_on = True
    laser.laser_beam = LaserBeam(laser.get_laser_point(), screen, laser.orientation, mirrors)
    return laser


def test_beam_orientation_follows_a_snap(lit_laser: Laser) -> None:
    lit_laser.set_orientation(180)

    assert lit_laser.laser_beam is not None
    assert lit_laser.laser_beam.orientation == 180


def test_beam_start_position_moves_with_a_snap(lit_laser: Laser) -> None:
    assert lit_laser.laser_beam is not None
    before = pygame.Vector2(lit_laser.laser_beam.start_pos)

    lit_laser.set_orientation(180)

    assert lit_laser.laser_beam.start_pos != before


def test_beam_path_recomputes_from_the_new_origin(lit_laser: Laser) -> None:
    lit_laser.set_orientation(180)
    assert lit_laser.laser_beam is not None
    expected_origin = lit_laser.laser_beam.start_pos

    lit_laser.laser_beam.update(0.016)

    assert (lit_laser.laser_beam.beam_path[0] - expected_origin).length() < 1.0


def test_beam_travels_in_the_new_direction(lit_laser: Laser) -> None:
    lit_laser.set_orientation(180)
    assert lit_laser.laser_beam is not None
    origin_x = lit_laser.laser_beam.start_pos.x

    lit_laser.laser_beam.update(0.016)

    assert lit_laser.laser_beam.beam_path[-1].x < origin_x


def test_snap_without_a_lit_beam_does_not_raise(screen: pygame.Surface) -> None:
    """set_orientation() must not assume laser_beam is set -- an unlit laser
    has laser_on=False and laser_beam=None."""
    laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
    laser.draw()

    laser.set_orientation(90)  # should not raise

    assert laser.orientation == 90


class TestBoundaryAndGrouping:
    """The two parameters levels added to LaserBeam. Both default to the
    behaviour the sandbox already relied on."""

    def test_a_beam_stops_at_the_table_edge_by_default(self, screen: pygame.Surface) -> None:
        mirrors: pygame.sprite.Group = pygame.sprite.Group()
        beam = LaserBeam(pygame.Vector2(100, 300), screen, 0, mirrors, add_to_groups=False)

        # Rightmost 1/6th of the screen is the sandbox's table
        assert beam.beam_path[-1].x == pytest.approx(screen.get_width() * 5 / 6)

    def test_an_explicit_boundary_lets_the_beam_run_further(self, screen: pygame.Surface) -> None:
        mirrors: pygame.sprite.Group = pygame.sprite.Group()
        beam = LaserBeam(
            pygame.Vector2(100, 300), screen, 0, mirrors,
            add_to_groups=False,
            right_boundary=screen.get_width(),
        )

        assert beam.beam_path[-1].x == pytest.approx(screen.get_width())

    def test_add_to_groups_false_keeps_the_beam_out_of_every_group(self, screen: pygame.Surface) -> None:
        mirrors: pygame.sprite.Group = pygame.sprite.Group()
        holder: pygame.sprite.Group = pygame.sprite.Group()
        LaserBeam.containers = (holder,)
        try:
            beam = LaserBeam(pygame.Vector2(100, 300), screen, 0, mirrors, add_to_groups=False)
            assert beam.groups() == []
            assert len(holder) == 0
        finally:
            del LaserBeam.containers

    def test_beams_still_join_their_containers_by_default(self, screen: pygame.Surface) -> None:
        mirrors: pygame.sprite.Group = pygame.sprite.Group()
        holder: pygame.sprite.Group = pygame.sprite.Group()
        LaserBeam.containers = (holder,)
        try:
            beam = LaserBeam(pygame.Vector2(100, 300), screen, 0, mirrors)
            assert beam in holder
        finally:
            del LaserBeam.containers
