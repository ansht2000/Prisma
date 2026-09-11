"""Unit tests for Target.is_hit_by, the win condition's core check."""
import pygame
import pytest

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
