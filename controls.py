"""The keyboard controls every piece that turns shares.

Mirrors, lasers and walls all rotate the same way -- hover one and hold A or
D -- so the rule for what those keys do, shift included, is written once here
rather than three times over.
"""
from typing import Protocol

import pygame

from constants import SLOW_ROTATION_FACTOR


class Rotatable(Protocol):
    """Structural type for anything the rotation keys can turn. Mirror, Laser
    and Wall all satisfy this without any of them importing this module's
    idea of a piece."""

    def rotate(self, dt: float) -> None: ...


def turn_with_keys(piece: Rotatable, dt: float) -> None:
    """Turns the piece for one frame according to the keys held down.

    A turns one way and D the other; holding shift slows the turn down, for
    settling on an angle that full speed overshoots.
    """
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        dt *= SLOW_ROTATION_FACTOR
    if keys[pygame.K_a]:
        piece.rotate(dt)
    if keys[pygame.K_d]:
        piece.rotate(-dt)
