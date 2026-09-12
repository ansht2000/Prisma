"""The name-this-level prompt the editor puts up when Save is clicked."""
from dataclasses import dataclass

import pygame

from button import Button
from constants import *
from render_utils import render_text


@dataclass(frozen=True)
class DialogResult:
    # What the dialog closed with. handle_event() returns None while it is
    # still open, so a caller only sees one of these once it is done.
    confirmed: bool
    name: str


class SaveDialog:
    # A modal box that reads a level name. Enter or the Save button confirm,
    # Escape or a click outside back out. Confirming with an empty box does
    # nothing -- there would be no name to save the file under.
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.text: str = ""
        self.font: pygame.font.Font = pygame.font.SysFont("Arial", NAME_DIALOG_FONT_SIZE)
        self.label_font: pygame.font.Font = pygame.font.SysFont("Arial", NAME_DIALOG_LABEL_FONT_SIZE)

        # Height follows what is stacked inside -- label, field, button, each
        # with its gap -- so the panel stays evenly padded if any of those change
        height = (
            NAME_DIALOG_PADDING + NAME_DIALOG_LABEL_FONT_SIZE
            + NAME_DIALOG_GAP + NAME_DIALOG_FIELD_HEIGHT
            + NAME_DIALOG_GAP + NAME_DIALOG_BUTTON_HEIGHT
            + NAME_DIALOG_PADDING
        )
        self.rect: pygame.Rect = pygame.Rect(0, 0, NAME_DIALOG_WIDTH, height)
        self.rect.center = (screen.get_width() // 2, screen.get_height() // 2)

        self.field_rect: pygame.Rect = pygame.Rect(
            self.rect.left + NAME_DIALOG_PADDING,
            self.rect.top + NAME_DIALOG_PADDING + NAME_DIALOG_LABEL_FONT_SIZE + NAME_DIALOG_GAP,
            NAME_DIALOG_WIDTH - 2 * NAME_DIALOG_PADDING,
            NAME_DIALOG_FIELD_HEIGHT,
        )
        self.save_button: Button = Button(
            EDITOR_SAVE_LABEL,
            pygame.Rect(
                self.rect.centerx - NAME_DIALOG_BUTTON_WIDTH // 2,
                self.field_rect.bottom + NAME_DIALOG_GAP,
                NAME_DIALOG_BUTTON_WIDTH,
                NAME_DIALOG_BUTTON_HEIGHT,
            ),
            self.label_font,
        )

    def handle_event(self, event: pygame.event.Event) -> DialogResult | None:
        # Returns None while the dialog should stay open
        if event.type == pygame.MOUSEMOTION:
            self.save_button.hovered = self.save_button.contains(event.pos)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.save_button.contains(event.pos):
                return self._confirm()
            if not self.rect.collidepoint(event.pos):
                return DialogResult(confirmed=False, name="")
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._confirm()
            if event.key == pygame.K_ESCAPE:
                return DialogResult(confirmed=False, name="")
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return None
            if len(self.text) < NAME_DIALOG_MAX_CHARS and self._is_allowed(event.unicode):
                self.text += event.unicode
            return None

        return None

    def _is_allowed(self, char: str) -> bool:
        # Anything printable: the file name is sanitised separately, so the
        # name the player sees does not have to be restricted to file syntax
        return len(char) == 1 and char.isprintable()

    def _confirm(self) -> DialogResult | None:
        if not self.text.strip():
            return None
        return DialogResult(confirmed=True, name=self.text.strip())

    def draw(self) -> None:
        pygame.draw.rect(self.screen, NAME_DIALOG_FILL, self.rect)
        pygame.draw.rect(self.screen, "white", self.rect, MENU_BORDER_WIDTH)

        label_text, label_rect = render_text(
            self.label_font, NAME_DIALOG_TITLE, NAME_DIALOG_LABEL_COLOR,
            (self.rect.centerx, self.rect.top + NAME_DIALOG_PADDING),
        )
        self.screen.blit(label_text, label_rect)

        pygame.draw.rect(self.screen, NAME_DIALOG_FIELD_FILL, self.field_rect)
        pygame.draw.rect(self.screen, "white", self.field_rect, MENU_BORDER_WIDTH)
        self._draw_entry()

        self.save_button.draw(self.screen)

    def _draw_entry(self) -> None:
        # The trailing caret makes it obvious the box is taking keystrokes
        entry = self.font.render(self.text + "|", True, MENU_ENABLED_COLOR)
        inner_width = self.field_rect.width - 2 * NAME_DIALOG_GAP
        left = self.field_rect.left + NAME_DIALOG_GAP
        top = self.field_rect.centery - entry.get_height() // 2
        if entry.get_width() <= inner_width:
            self.screen.blit(entry, (left, top))
            return
        # A name too long for the field scrolls, keeping the caret in view
        visible = pygame.Rect(
            entry.get_width() - inner_width, 0, inner_width, entry.get_height()
        )
        self.screen.blit(entry, (left, top), visible)
