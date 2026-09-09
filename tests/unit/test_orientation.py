"""Unit tests for Mirror.set_orientation / Laser.set_orientation.

Exercises the plain wrap-and-set behaviour in isolation, with no event loop
and no InputBox involved.
"""
import pygame
import pytest

from mirror import Mirror
from laser import Laser

pytestmark = pytest.mark.unit


class TestMirrorSetOrientation:
    def test_sets_a_plain_value(self, screen):
        mirror = Mirror(400, 300, screen, add_to_groups=False)
        mirror.draw()

        mirror.set_orientation(90)

        assert mirror.orientation == 90

    def test_wraps_values_above_360(self, screen):
        mirror = Mirror(400, 300, screen, add_to_groups=False)
        mirror.draw()

        mirror.set_orientation(450)

        assert mirror.orientation == 90

    def test_wraps_negative_values(self, screen):
        mirror = Mirror(400, 300, screen, add_to_groups=False)
        mirror.draw()

        mirror.set_orientation(-90)

        assert mirror.orientation == 270

    def test_accepts_fractional_degrees(self, screen):
        mirror = Mirror(400, 300, screen, add_to_groups=False)
        mirror.draw()

        mirror.set_orientation(22.5)

        assert mirror.orientation == 22.5


class TestLaserSetOrientation:
    def test_sets_a_plain_value(self, screen):
        laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
        laser.draw()

        laser.set_orientation(135)

        assert laser.orientation == 135

    def test_wraps_values_above_360(self, screen):
        laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
        laser.draw()

        laser.set_orientation(400)

        assert laser.orientation == 40

    def test_wraps_negative_values(self, screen):
        laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
        laser.draw()

        laser.set_orientation(-30)

        assert laser.orientation == 330

    def test_refreshes_corners_immediately(self, screen):
        """get_laser_point() reads corner attributes that only draw() used to
        refresh -- set_orientation() must recompute them itself, or the emitter
        point stays stale until the next frame's draw() call."""
        laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
        laser.draw()
        before = laser.get_laser_point()

        laser.set_orientation(180)

        after = laser.get_laser_point()
        assert before != after
        # Flipping 180 degrees puts the emitter on the opposite edge of the body.
        expected = pygame.Vector2(400 - laser.length / 2, 300)
        assert (after - expected).length() < 1.0

    def test_draw_agrees_with_the_snap(self, screen):
        """A subsequent draw() should not move the emitter again -- it must
        already reflect the snapped orientation."""
        laser = Laser(400, 300, screen, orientation=0, add_to_groups=False)
        laser.draw()

        laser.set_orientation(180)
        after_snap = laser.get_laser_point()
        laser.draw()
        after_draw = laser.get_laser_point()

        assert (after_draw - after_snap).length() < 1.0
