"""Unit tests for SaveDialog: the name prompt the editor puts up when Save is
clicked. Covers typing, both ways of confirming, and both ways of backing out.
"""
import pygame
import pytest

from save_dialog import DialogResult, SaveDialog

pytestmark = pytest.mark.unit


def key(dialog: SaveDialog, code: int, unicode: str = "") -> DialogResult | None:
    return dialog.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": code, "unicode": unicode}))


def type_text(dialog: SaveDialog, text: str) -> None:
    for char in text:
        key(dialog, ord(char), char)


def click(dialog: SaveDialog, pos: tuple[float, float]) -> DialogResult | None:
    return dialog.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    )


class TestTyping:
    def test_typed_characters_land_in_the_box(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        type_text(dialog, "bounce")

        assert dialog.text == "bounce"

    def test_spaces_and_punctuation_are_allowed(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        type_text(dialog, "two-way split!")

        assert dialog.text == "two-way split!"

    def test_backspace_deletes_the_last_character(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "abc")

        key(dialog, pygame.K_BACKSPACE)

        assert dialog.text == "ab"

    def test_backspace_on_an_empty_box_is_harmless(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        key(dialog, pygame.K_BACKSPACE)

        assert dialog.text == ""

    def test_the_name_has_a_length_limit(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        type_text(dialog, "x" * 200)

        assert len(dialog.text) == 32

    def test_typing_leaves_the_dialog_open(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        assert key(dialog, ord("a"), "a") is None


class TestConfirming:
    def test_enter_confirms_with_the_typed_name(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "bounce")

        result = key(dialog, pygame.K_RETURN)

        assert result is not None
        assert (result.confirmed, result.name) == (True, "bounce")

    def test_the_save_button_confirms_too(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "bounce")

        result = click(dialog, dialog.save_button.rect.center)

        assert result is not None
        assert (result.confirmed, result.name) == (True, "bounce")

    def test_surrounding_whitespace_is_trimmed_off_the_name(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "  bounce  ")

        result = key(dialog, pygame.K_RETURN)

        assert result is not None
        assert result.name == "bounce"

    def test_confirming_an_empty_name_keeps_the_dialog_open(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        assert key(dialog, pygame.K_RETURN) is None
        assert click(dialog, dialog.save_button.rect.center) is None

    def test_confirming_a_blank_name_keeps_the_dialog_open(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "   ")

        assert key(dialog, pygame.K_RETURN) is None


class TestCancelling:
    def test_escape_backs_out(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "bounce")

        result = key(dialog, pygame.K_ESCAPE)

        assert result is not None
        assert result.confirmed is False

    def test_clicking_outside_the_panel_backs_out(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        result = click(dialog, (2, 2))

        assert result is not None
        assert result.confirmed is False

    def test_clicking_inside_the_panel_keeps_it_open(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        assert click(dialog, dialog.field_rect.center) is None


class TestLayout:
    def test_the_save_button_sits_under_the_text_field(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        assert dialog.save_button.rect.top >= dialog.field_rect.bottom
        assert dialog.rect.contains(dialog.save_button.rect)

    def test_the_panel_is_centered_on_the_screen(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)

        assert dialog.rect.center == (screen.get_width() // 2, screen.get_height() // 2)

    def test_a_name_too_long_for_the_field_still_draws(self, screen: pygame.Surface) -> None:
        dialog = SaveDialog(screen)
        type_text(dialog, "W" * 32)

        dialog.draw()  # must not raise
