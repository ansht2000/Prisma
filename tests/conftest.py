"""Shared pytest fixtures for the Prisma test suite.

SDL_VIDEODRIVER must be set to "dummy" before pygame is imported anywhere,
so it lives here rather than in a fixture -- fixtures run too late.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from constants import SCREEN_WIDTH, SCREEN_HEIGHT


@pytest.fixture
def screen():
    """A real pygame surface (backed by the dummy driver) for objects that draw."""
    pygame.init()
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield surface
    pygame.display.quit()
