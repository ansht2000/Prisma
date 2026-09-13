"""Unit tests for the rotation keys every turnable piece shares: which way A
and D turn a piece, and shift slowing the turn down.

The keyboard is stood in for rather than really pressed -- pygame reports no
keys held under the dummy driver.
"""
from typing import Callable

import pygame
import pytest

from constants import ROTATION_SPEED, SLOW_ROTATION_FACTOR
from controls import turn_with_keys
from laser import Laser
from mirror import Mirror
from wall import Wall

pytestmark = pytest.mark.unit

FRAME = 1.0  # a whole second of turning, so the numbers are easy to read

# Says which keys are being held down for the rest of the test
HoldKeys = Callable[..., None]


class FakeKeys:
    """Stands in for pygame.key.get_pressed(), reporting the given keys held."""

    def __init__(self, *held: int) -> None:
        self.held: set[int] = set(held)

    def __getitem__(self, key: int) -> bool:
        return key in self.held


@pytest.fixture
def hold(monkeypatch: pytest.MonkeyPatch) -> HoldKeys:
    def press(*keys: int) -> None:
        monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakeKeys(*keys))

    return press


class Spy:
    """A stand-in piece that only records how far it was asked to turn."""

    def __init__(self) -> None:
        self.turned: float = 0

    def rotate(self, dt: float) -> None:
        self.turned += dt


class TestWhichWayItTurns:
    def test_a_turns_one_way(self, hold: HoldKeys) -> None:
        hold(pygame.K_a)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == FRAME

    def test_d_turns_the_other(self, hold: HoldKeys) -> None:
        hold(pygame.K_d)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == -FRAME

    def test_no_keys_leaves_it_alone(self, hold: HoldKeys) -> None:
        hold()
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == 0

    def test_both_keys_cancel_out(self, hold: HoldKeys) -> None:
        hold(pygame.K_a, pygame.K_d)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == 0


class TestShiftSlowsItDown:
    def test_shift_turns_it_more_slowly(self, hold: HoldKeys) -> None:
        hold(pygame.K_a, pygame.K_LSHIFT)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == pytest.approx(FRAME * SLOW_ROTATION_FACTOR)

    def test_it_is_30_percent_slower(self, hold: HoldKeys) -> None:
        hold(pygame.K_a)
        full = Spy()
        turn_with_keys(full, FRAME)
        hold(pygame.K_a, pygame.K_LSHIFT)
        slowed = Spy()

        turn_with_keys(slowed, FRAME)

        assert slowed.turned == pytest.approx(full.turned * 0.7)

    def test_the_right_shift_key_works_too(self, hold: HoldKeys) -> None:
        hold(pygame.K_d, pygame.K_RSHIFT)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == pytest.approx(-FRAME * SLOW_ROTATION_FACTOR)

    def test_shift_on_its_own_turns_nothing(self, hold: HoldKeys) -> None:
        hold(pygame.K_LSHIFT)
        piece = Spy()

        turn_with_keys(piece, FRAME)

        assert piece.turned == 0


class TestEveryPieceObeysIt:
    """Mirror, laser and wall all rotate through the same rule."""

    def pieces(self, screen: pygame.Surface) -> list[Mirror | Laser | Wall]:
        return [
            Mirror(400, 300, screen, add_to_groups=False),
            Laser(400, 300, screen, add_to_groups=False),
            Wall(400, 300, screen, add_to_groups=False),
        ]

    def hover(self, piece: Mirror | Laser | Wall, monkeypatch: pytest.MonkeyPatch) -> None:
        piece.draw()  # gives the piece the hitbox update() checks the pointer against
        assert piece.rect is not None
        monkeypatch.setattr(pygame.mouse, "get_pos", lambda: piece.rect.center)

    def test_a_hovered_piece_turns_at_full_speed(
        self, screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch, hold: HoldKeys
    ) -> None:
        hold(pygame.K_a)

        for piece in self.pieces(screen):
            self.hover(piece, monkeypatch)
            piece.orientation = 0

            piece.update(1.0)

            assert piece.orientation == pytest.approx(ROTATION_SPEED)

    def test_shift_slows_every_one_of_them(
        self, screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch, hold: HoldKeys
    ) -> None:
        hold(pygame.K_a, pygame.K_LSHIFT)

        for piece in self.pieces(screen):
            self.hover(piece, monkeypatch)
            piece.orientation = 0

            piece.update(1.0)

            assert piece.orientation == pytest.approx(ROTATION_SPEED * SLOW_ROTATION_FACTOR)

    def test_a_piece_the_pointer_is_not_on_ignores_the_keys(
        self, screen: pygame.Surface, monkeypatch: pytest.MonkeyPatch, hold: HoldKeys
    ) -> None:
        hold(pygame.K_a)
        monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (5, 5))

        for piece in self.pieces(screen):
            piece.draw()
            piece.orientation = 0

            piece.update(1.0)

            assert piece.orientation == 0
