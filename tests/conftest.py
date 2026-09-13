"""Shared pytest fixtures for the Prisma test suite.

Two things in here apply to every test in the suite whether it asks for them
or not, so they are worth knowing before writing a new one:

1. SDL_VIDEODRIVER is set to "dummy" before pygame is imported anywhere. That
   happens at module level rather than in a fixture -- fixtures run too late.

2. Targets charge instantly. In the game a target has to be held in the beam
   for TARGET_CHARGE_SECONDS before the level is won (see Target.advance);
   the autouse instant_target_charge fixture below cuts that to nothing, so a
   test that finishes a level needs no mention of time at all:

       only_mirror(level).set_orientation(SOLVING_ANGLE)
       run_frame(level)
       assert level.won is True

   A test that is about the timing asks for the real_target_charge fixture,
   which puts the real duration back for that test and hands it over in
   seconds. A whole class opts in with one fixture:

       @pytest.fixture(autouse=True)
       def use_the_real_charge_time(self, real_target_charge: float) -> None:
           pass

   TestCharging in tests/unit/test_target.py and TestHoldingTheBeamOnTheTarget
   in tests/unit/test_level.py are the two places that do this; everywhere
   else in the suite is better off not knowing the timer exists.
"""
import os
from typing import Iterator

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

import target
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_CHARGE_SECONDS

# Short enough that any single frame fills a target completely
INSTANT_CHARGE_SECONDS: float = 0.001


@pytest.fixture
def screen() -> Iterator[pygame.Surface]:
    """A real pygame surface (backed by the dummy driver) for objects that draw."""
    pygame.init()
    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    yield surface
    pygame.display.quit()


@pytest.fixture(autouse=True)
def instant_target_charge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Targets fill as soon as the beam reaches them -- see the note at the
    top of this file, and real_target_charge below for the way out of it."""
    monkeypatch.setattr(target, "TARGET_CHARGE_SECONDS", INSTANT_CHARGE_SECONDS)


@pytest.fixture
def real_target_charge(monkeypatch: pytest.MonkeyPatch) -> float:
    """Restores the real charge time, and hands it to the test in seconds."""
    monkeypatch.setattr(target, "TARGET_CHARGE_SECONDS", TARGET_CHARGE_SECONDS)
    return TARGET_CHARGE_SECONDS
