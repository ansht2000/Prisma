"""Unit tests for LoadDialog: the list of levels the editor can open.

It reports what was picked and leaves the opening to the editor, so these
tests only look at what comes back out of handle_event().
"""
from pathlib import Path

import pygame
import pytest

from custom_levels import CustomLevel, SavedLevel
from load_dialog import LoadDialog, LoadResult

pytestmark = pytest.mark.unit


def saved(name: str, directory: Path) -> SavedLevel:
    return SavedLevel(directory / f"{name}.toml", CustomLevel(name=name))


def click(dialog: LoadDialog, pos: tuple[float, float]) -> LoadResult | None:
    return dialog.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    )


def escape(dialog: LoadDialog) -> LoadResult | None:
    return dialog.handle_event(
        pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE, "unicode": ""})
    )


class TestListing:
    def test_one_box_per_level(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path), saved("two", tmp_path)])

        assert [b.label for b in dialog.buttons] == ["one", "two"]

    def test_a_long_name_is_shortened_to_fit(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("an extremely long level name", tmp_path)])

        label = dialog.buttons[0].label
        assert label.endswith("...")
        assert dialog.box_font.size(label)[0] <= dialog.buttons[0].rect.width

    def test_boxes_start_below_the_heading(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        title_bottom = dialog.title_center[1] + dialog.title_font.get_height() // 2
        assert dialog.buttons[0].rect.top >= title_bottom

    def test_the_cancel_button_sits_below_the_boxes(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        assert dialog.cancel_button.rect.top >= dialog.buttons[0].rect.bottom
        assert dialog.cancel_button.rect.bottom <= screen.get_height()

    def test_cancel_stays_on_screen_with_a_long_list(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        dialog = LoadDialog(screen, [saved(f"level{n:02d}", tmp_path) for n in range(24)])

        assert dialog.cancel_button.rect.bottom <= screen.get_height()

    def test_an_empty_list_still_draws(self, screen: pygame.Surface) -> None:
        dialog = LoadDialog(screen, [])

        assert dialog.buttons == []
        dialog.draw()  # must not raise


class TestPicking:
    def test_clicking_a_box_picks_that_level(self, screen: pygame.Surface, tmp_path: Path) -> None:
        entries = [saved("one", tmp_path), saved("two", tmp_path)]
        dialog = LoadDialog(screen, entries)

        result = click(dialog, dialog.buttons[1].rect.center)

        assert result is not None
        assert result.chosen == entries[1]

    def test_the_file_comes_back_with_the_level(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        result = click(dialog, dialog.buttons[0].rect.center)

        assert result is not None
        assert result.chosen is not None
        assert result.chosen.path == tmp_path / "one.toml"

    def test_clicking_empty_space_keeps_it_open(
        self, screen: pygame.Surface, tmp_path: Path
    ) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        assert click(dialog, (screen.get_width() - 5, screen.get_height() - 5)) is None


class TestCancelling:
    def test_the_cancel_button_backs_out(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        result = click(dialog, dialog.cancel_button.rect.center)

        assert result is not None
        assert result.chosen is None

    def test_escape_backs_out(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])

        result = escape(dialog)

        assert result is not None
        assert result.chosen is None

    def test_hover_tracks_the_pointer(self, screen: pygame.Surface, tmp_path: Path) -> None:
        dialog = LoadDialog(screen, [saved("one", tmp_path)])
        box = dialog.buttons[0]

        dialog.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": box.rect.center}))
        assert box.hovered is True

        dialog.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5)}))
        assert box.hovered is False
