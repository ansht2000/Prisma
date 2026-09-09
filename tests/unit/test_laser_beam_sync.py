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
def lit_laser(screen):
    laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
    laser.draw()
    mirrors = pygame.sprite.Group()  # empty: beam travels unobstructed
    laser.laser_on = True
    laser.laser_beam = LaserBeam(laser.get_laser_point(), screen, laser.orientation, mirrors)
    return laser


def test_beam_orientation_follows_a_snap(lit_laser):
    lit_laser.set_orientation(180)

    assert lit_laser.laser_beam.orientation == 180


def test_beam_start_position_moves_with_a_snap(lit_laser):
    before = pygame.Vector2(lit_laser.laser_beam.start_pos)

    lit_laser.set_orientation(180)

    assert lit_laser.laser_beam.start_pos != before


def test_beam_path_recomputes_from_the_new_origin(lit_laser):
    lit_laser.set_orientation(180)
    expected_origin = lit_laser.laser_beam.start_pos

    lit_laser.laser_beam.update(0.016)

    assert (lit_laser.laser_beam.beam_path[0] - expected_origin).length() < 1.0


def test_beam_travels_in_the_new_direction(lit_laser):
    lit_laser.set_orientation(180)
    origin_x = lit_laser.laser_beam.start_pos.x

    lit_laser.laser_beam.update(0.016)

    assert lit_laser.laser_beam.beam_path[-1].x < origin_x


def test_snap_without_a_lit_beam_does_not_raise(screen):
    """set_orientation() must not assume laser_beam is set -- an unlit laser
    has laser_on=False and laser_beam=None."""
    laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
    laser.draw()

    laser.set_orientation(90)  # should not raise

    assert laser.orientation == 90
