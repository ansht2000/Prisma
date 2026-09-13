"""The pick-a-level prompt the editor puts up when Load is clicked.

Modal rather than a screen of its own: the editor keeps its board while the
list is open, so backing out leaves the work in progress untouched. The levels
are laid out by the same rules as the custom level select screen, so the two
lists read the same way.
"""
from dataclasses import dataclass

import pygame

from button import Button
from constants import *
from custom_levels import SavedLevel
from level_select import layout_boxes
from render_utils import fit_text, render_text


@dataclass(frozen=True)
class LoadResult:
    # What the dialog closed with. handle_event() returns None while it is
    # still open; `chosen` is None when the dialog was backed out of.
    chosen: SavedLevel | None


class LoadDialog:
    # A dimmed, full-screen list of the levels that can be opened. Clicking
    # one picks it; Cancel or Escape backs out.
    def __init__(self, screen: pygame.Surface, saved: list[SavedLevel]) -> None:
        self.screen: pygame.Surface = screen
        self.saved: list[SavedLevel] = saved
        self.title_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_TITLE_FONT_SIZE)
        self.box_font: pygame.font.Font = pygame.font.SysFont("Arial", CUSTOM_BOX_FONT_SIZE)
        self.button_font: pygame.font.Font = pygame.font.SysFont("Arial", EDITOR_SAVE_FONT_SIZE)

        rects, self.title_center = layout_boxes(
            screen,
            self.title_font,
            len(saved),
            box_width=CUSTOM_BOX_WIDTH,
            box_height=LEVEL_BOX_SIZE,
        )
        self.buttons: list[Button] = [
            Button(
                # Names are the player's own, and can be longer than the box
                fit_text(self.box_font, entry.level.name, CUSTOM_BOX_WIDTH - 2 * LEVEL_BOX_SPACING),
                rect,
                self.box_font,
            )
            for entry, rect in zip(saved, rects)
        ]
        self.cancel_button: Button = Button(
            LOAD_DIALOG_CANCEL_LABEL, self._cancel_rect(rects), self.button_font
        )

    def _cancel_rect(self, rects: list[pygame.Rect]) -> pygame.Rect:
        # Just under the last row of levels, and never off the bottom of the
        # screen however many rows there turn out to be
        below = max((rect.bottom for rect in rects), default=self.title_center[1])
        top = min(
            int(below) + LEVEL_BOX_SPACING * 2,
            self.screen.get_height() - LEVEL_BOX_MARGIN - EDITOR_SAVE_BUTTON_HEIGHT,
        )
        return pygame.Rect(
            (self.screen.get_width() - EDITOR_SAVE_BUTTON_WIDTH) // 2,
            top,
            EDITOR_SAVE_BUTTON_WIDTH,
            EDITOR_SAVE_BUTTON_HEIGHT,
        )

    def handle_event(self, event: pygame.event.Event) -> LoadResult | None:
        # Returns None while the dialog should stay open
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.hovered = button.contains(event.pos)
            self.cancel_button.hovered = self.cancel_button.contains(event.pos)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for entry, button in zip(self.saved, self.buttons):
                if button.contains(event.pos):
                    return LoadResult(chosen=entry)
            if self.cancel_button.contains(event.pos):
                return LoadResult(chosen=None)
            return None

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return LoadResult(chosen=None)

        return None

    def draw(self) -> None:
        # Dim the editor underneath so the list reads as modal
        dim = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, OVERLAY_DIM_ALPHA))
        self.screen.blit(dim, (0, 0))

        title_text, title_rect = render_text(
            self.title_font, LOAD_DIALOG_TITLE, MENU_ENABLED_COLOR, self.title_center
        )
        self.screen.blit(title_text, title_rect)

        for button in self.buttons:
            button.draw(self.screen)
        self.cancel_button.draw(self.screen)
