"""Unit tests for the level registry: looking levels up and walking forward
through them. This is the data that makes "Next Level" light up on its own
once a second level is added.
"""
import pytest

import levels
from levels import LEVEL_ONE, LEVELS, LevelLayout, MirrorSpec, level_by_number, next_level

pytestmark = pytest.mark.unit


def make_layout(number: int) -> LevelLayout:
    return LevelLayout(
        number=number,
        hint="",
        laser_cell=(0, 2),
        laser_orientation=0,
        target_cell=(4, 0),
        mirrors=(MirrorSpec(cell=(4, 2), orientation=90),),
    )


class TestRegistry:
    def test_ships_exactly_one_level_for_now(self) -> None:
        assert [layout.number for layout in LEVELS] == [1]

    def test_level_by_number_finds_level_one(self) -> None:
        assert level_by_number(1) is LEVEL_ONE

    def test_level_by_number_returns_none_for_an_unknown_level(self) -> None:
        assert level_by_number(99) is None


class TestNextLevel:
    def test_the_last_level_has_no_next(self) -> None:
        assert next_level(LEVEL_ONE) is None

    def test_next_level_follows_registry_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        one, two = make_layout(1), make_layout(2)
        monkeypatch.setattr(levels, "LEVELS", [one, two])

        assert next_level(one) is two
        assert next_level(two) is None

    def test_a_layout_outside_the_registry_has_no_next(self) -> None:
        assert next_level(make_layout(42)) is None
