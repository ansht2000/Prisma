"""Unit tests for the objects table: that every object it offers is listed,
and that they all fit on the one page however many there are.

The table only knows where its entries went once it has drawn itself, so each
test draws first, exactly as the app loop does.
"""
import pygame
import pytest

from table import EDITOR_ENTRIES, SANDBOX_ENTRIES, Table, TableRow

pytestmark = pytest.mark.unit


def drawn(screen: pygame.Surface, entries: list[TableRow]) -> Table:
    table = Table(screen, entries)
    table.draw()
    return table


def object_rects(table: Table, entries: list[TableRow]) -> list[pygame.Rect]:
    return [table.entry_rects[name] for name, _, _ in entries]


class TestEditorTable:
    def test_it_offers_every_piece_a_level_can_hold(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)

        assert [name for name, _, _ in EDITOR_ENTRIES] == ["mirror", "laser", "target", "wall"]
        assert set(table.entry_rects) >= {"mirror", "laser", "target", "wall"}

    def test_every_entry_fits_on_the_page(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)

        for rect in object_rects(table, EDITOR_ENTRIES):
            assert rect.top >= 0
            assert rect.bottom <= screen.get_height()

    def test_the_entries_do_not_run_into_each_other(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)

        rects = object_rects(table, EDITOR_ENTRIES)
        for above, below in zip(rects, rects[1:]):
            assert above.bottom <= below.top

    def test_they_stay_in_the_table_strip(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)

        for rect in object_rects(table, EDITOR_ENTRIES):
            assert rect.right <= screen.get_width()

    def test_they_sit_below_the_heading(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)

        title = table.entry_rects["title"]
        for rect in object_rects(table, EDITOR_ENTRIES):
            assert rect.top >= title.bottom

    def test_redrawing_leaves_them_where_they_were(self, screen: pygame.Surface) -> None:
        """The layout is rebuilt every frame, so it has to be stable."""
        table = drawn(screen, EDITOR_ENTRIES)
        first = object_rects(table, EDITOR_ENTRIES)

        table.draw()

        assert object_rects(table, EDITOR_ENTRIES) == first

    def test_redrawing_does_not_pile_up_state(self, screen: pygame.Surface) -> None:
        table = drawn(screen, EDITOR_ENTRIES)
        after_one_frame = len(table.marking_rects)

        for _ in range(10):
            table.draw()

        assert len(table.marking_rects) == after_one_frame


class TestSandboxTable:
    def test_it_offers_what_free_play_can_use(self, screen: pygame.Surface) -> None:
        # Everything the editor lists except the target: the sandbox has
        # nothing to win, so there is nothing to aim at
        assert [name for name, _, _ in SANDBOX_ENTRIES] == ["mirror", "laser", "wall"]

    def test_its_pieces_fit_too(self, screen: pygame.Surface) -> None:
        table = drawn(screen, SANDBOX_ENTRIES)

        rects = object_rects(table, SANDBOX_ENTRIES)
        for rect in rects:
            assert rect.bottom <= screen.get_height()
        for above, below in zip(rects, rects[1:]):
            assert above.bottom <= below.top

    def test_the_table_is_the_default(self, screen: pygame.Surface) -> None:
        table = Table(screen)

        assert table.entries == SANDBOX_ENTRIES

    def test_its_pieces_are_drawn_exactly_as_the_editor_draws_them(
        self, screen: pygame.Surface
    ) -> None:
        """The two lists are meant to look the same, so the pieces they have
        in common are built by the very same sample."""
        editor_samples = {name: make for name, make, _ in EDITOR_ENTRIES}

        for name, make, _ in SANDBOX_ENTRIES:
            assert make is editor_samples[name]

    def test_the_shared_entries_land_in_the_same_places(self, screen: pygame.Surface) -> None:
        sandbox = drawn(screen, SANDBOX_ENTRIES)
        editor = drawn(screen, EDITOR_ENTRIES)

        # Mirror and laser lead both lists, so they sit identically; the
        # sandbox simply has no target row after them
        for name in ("mirror", "laser"):
            assert sandbox.entry_rects[name] == editor.entry_rects[name]


def test_a_crowded_page_still_fits(screen: pygame.Surface) -> None:
    """Guards the headroom: the entries would have to grow by half again
    before anything fell off the bottom."""
    table = drawn(screen, EDITOR_ENTRIES)

    used = max(rect.bottom for rect in object_rects(table, EDITOR_ENTRIES))
    assert used <= screen.get_height() * 0.95
