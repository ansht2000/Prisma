"""Unit tests for Target: the beam check at the heart of the win condition,
and the charge a beam has to hold on it before that win is given.
"""
import pygame
import pytest

from constants import TARGET_CHARGE_COLOR, TARGET_CHARGE_SECONDS, TARGET_COLOR
from target import Target

pytestmark = pytest.mark.unit


@pytest.fixture
def target(screen: pygame.Surface) -> Target:
    return Target(400, 300, screen, size=40)


def path(*points: tuple[float, float]) -> list[pygame.Vector2]:
    return [pygame.Vector2(p) for p in points]


def test_a_beam_straight_through_is_a_hit(target: Target) -> None:
    assert target.is_hit_by(path((0, 300), (800, 300))) is True


def test_a_beam_that_misses_is_not_a_hit(target: Target) -> None:
    assert target.is_hit_by(path((0, 50), (800, 50))) is False


def test_a_beam_stopping_short_is_not_a_hit(target: Target) -> None:
    assert target.is_hit_by(path((0, 300), (300, 300))) is False


def test_a_hit_on_a_later_segment_counts(target: Target) -> None:
    # Travels right well below the target, turns up, then crosses it
    assert target.is_hit_by(path((0, 600), (400, 600), (400, 0))) is True


def test_an_empty_path_is_not_a_hit(target: Target) -> None:
    assert target.is_hit_by([]) is False


def test_a_single_point_path_is_not_a_hit(target: Target) -> None:
    assert target.is_hit_by(path((400, 300))) is False


def test_the_target_is_centred_on_its_position(target: Target) -> None:
    assert target.rect.center == (400, 300)


class TestCharging:
    """These are the tests the charge time actually matters to, so they put
    the real duration back (see tests/conftest.py)."""

    @pytest.fixture(autouse=True)
    def use_the_real_charge_time(self, real_target_charge: float) -> None:
        pass

    def test_it_starts_empty(self, target: Target) -> None:
        assert target.charge == 0
        assert target.is_charged is False

    def test_the_beam_fills_it_over_time(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 4, lit=True)

        assert target.charge == pytest.approx(0.25)

    def test_it_is_not_charged_part_way_through(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS - 0.1, lit=True)

        assert target.is_charged is False

    def test_it_fills_after_the_full_time(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS, lit=True)

        assert target.is_charged is True

    def test_it_fills_the_same_way_frame_by_frame(self, target: Target) -> None:
        frame = TARGET_CHARGE_SECONDS / 100
        for _ in range(100):
            target.advance(frame, lit=True)

        assert target.is_charged is True

    def test_it_never_overfills(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS * 10, lit=True)

        assert target.charge == 1.0

    def test_taking_the_beam_off_starts_it_draining(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)

        target.advance(TARGET_CHARGE_SECONDS / 4, lit=False)

        assert target.charge == pytest.approx(0.25)

    def test_it_drains_at_the_pace_it_fills(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)

        target.advance(TARGET_CHARGE_SECONDS / 2, lit=False)

        assert target.charge == 0

    def test_a_moment_off_the_beam_costs_only_that_moment(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS * 0.9, lit=True)

        target.advance(0.016, lit=False)

        assert target.charge == pytest.approx(0.9 - 0.016 / TARGET_CHARGE_SECONDS)

    def test_putting_the_beam_back_carries_on_from_where_it_got_to(
        self, target: Target
    ) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)
        target.advance(TARGET_CHARGE_SECONDS / 4, lit=False)

        target.advance(TARGET_CHARGE_SECONDS / 4, lit=True)

        assert target.charge == pytest.approx(0.5)

    def test_it_never_drains_past_empty(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)

        target.advance(TARGET_CHARGE_SECONDS * 10, lit=False)

        assert target.charge == 0

    def test_a_target_left_alone_stays_empty(self, target: Target) -> None:
        target.advance(TARGET_CHARGE_SECONDS * 2, lit=False)

        assert target.charge == 0


class TestDrawing:
    @pytest.fixture(autouse=True)
    def use_the_real_charge_time(self, real_target_charge: float) -> None:
        pass

    def test_an_empty_target_is_all_its_own_colour(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        screen.fill("black")

        target.draw()

        assert screen.get_at((target.rect.centerx, target.rect.top + 1))[:3] == TARGET_COLOR
        assert screen.get_at((target.rect.centerx, target.rect.bottom - 2))[:3] == TARGET_COLOR

    def test_a_full_target_is_all_fill_colour(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        screen.fill("black")
        target.advance(TARGET_CHARGE_SECONDS, lit=True)

        target.draw()

        assert screen.get_at((target.rect.centerx, target.rect.top + 1))[:3] == TARGET_CHARGE_COLOR
        assert screen.get_at((target.rect.centerx, target.rect.bottom - 2))[:3] == TARGET_CHARGE_COLOR

    def test_it_fills_from_the_bottom_up(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        screen.fill("black")
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)

        target.draw()

        # The bottom half has turned, the top half has not
        assert screen.get_at((target.rect.centerx, target.rect.bottom - 2))[:3] == TARGET_CHARGE_COLOR
        assert screen.get_at((target.rect.centerx, target.rect.top + 1))[:3] == TARGET_COLOR

    def test_the_fill_line_climbs_as_it_charges(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        def filled_pixels() -> int:
            screen.fill("black")
            target.draw()
            column = target.rect.centerx
            return sum(
                1
                for y in range(target.rect.top, target.rect.bottom)
                if screen.get_at((column, y))[:3] == TARGET_CHARGE_COLOR
            )

        target.advance(TARGET_CHARGE_SECONDS / 4, lit=True)
        quarter = filled_pixels()
        target.advance(TARGET_CHARGE_SECONDS / 4, lit=True)
        half = filled_pixels()

        assert 0 < quarter < half < target.rect.height

    def test_draining_it_puts_the_colour_back(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=False)
        screen.fill("black")

        target.draw()

        assert screen.get_at((target.rect.centerx, target.rect.bottom - 2))[:3] == TARGET_COLOR

    def test_drawing_does_not_leave_the_screen_clipped(
        self, target: Target, screen: pygame.Surface
    ) -> None:
        """Everything drawn after the target would vanish if it did."""
        before = screen.get_clip()
        target.advance(TARGET_CHARGE_SECONDS / 2, lit=True)

        target.draw()

        assert screen.get_clip() == before
