"""The list of levels the player has built in the level editor.

Laid out by the same rules as the built-in level select (see
level_select.layout_boxes), except that a box carries the name the level was
saved under rather than a number. A level saved without everything it needs to
be playable is still listed, just greyed out.
"""
from pathlib import Path

import pygame

from button import Button
from constants import *
from custom_levels import CUSTOM_LEVELS_DIR, CustomLevel, load_all, to_layout
from level_select import layout_boxes
from levels import LevelLayout
from render_utils import fit_text, render_text
from scene import Scene


class CustomLevelSelectScene(Scene):
    def __init__(
        self,
        screen: pygame.Surface,
        levels: list[CustomLevel] | None = None,
        directory: Path | None = None,
    ) -> None:
        super().__init__(screen)
        # Both injectable so a test can work off its own directory, or skip
        # the disk entirely and hand the screen its levels directly
        self.directory: Path = CUSTOM_LEVELS_DIR if directory is None else directory
        self.levels: list[CustomLevel] = load_all(self.directory) if levels is None else levels

        # The playable ones, numbered by their place in that set, so that
        # finishing one offers the next custom level rather than a built-in
        self.playlist: list[LevelLayout] = []
        # Parallel to self.levels: the layout to play, or None if it cannot be
        self.layouts: list[LevelLayout | None] = []
        for level in self.levels:
            layout = to_layout(level, len(self.playlist) + 1)
            self.layouts.append(layout)
            if layout is not None:
                self.playlist.append(layout)

        self.title_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_TITLE_FONT_SIZE)
        self.box_font: pygame.font.Font = pygame.font.SysFont("Arial", CUSTOM_BOX_FONT_SIZE)
        self.empty_font: pygame.font.Font = pygame.font.SysFont("Arial", CUSTOM_EMPTY_FONT_SIZE)
        self.buttons: list[Button] = []
        self.title_center: tuple[float, float] = (0, 0)
        self._layout()

    def _layout(self) -> None:
        rects, self.title_center = layout_boxes(
            self.screen,
            self.title_font,
            len(self.levels),
            box_width=CUSTOM_BOX_WIDTH,
            box_height=LEVEL_BOX_SIZE,
        )
        self.buttons = [
            Button(
                # Names are the player's own, and can be longer than the box
                fit_text(self.box_font, level.name, CUSTOM_BOX_WIDTH - 2 * LEVEL_BOX_SPACING),
                rect,
                self.box_font,
                enabled=layout is not None,
            )
            for level, layout, rect in zip(self.levels, self.layouts, rects)
        ]

    def start_level(self, layout: LevelLayout) -> None:
        from level import LevelScene  # local import: LevelScene navigates back here

        directory = self.directory
        self.go_to(
            LevelScene(
                self.screen,
                layout,
                self.playlist,
                # Rebuilt rather than captured, so a level saved or removed in
                # the meantime shows up when the player comes back
                lambda screen: CustomLevelSelectScene(screen, directory=directory),
            )
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._layout()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from menu import MenuScene  # local import: the menu opens this screen

            self.go_to(MenuScene(self.screen))
            return

        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.hovered = button.contains(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for layout, button in zip(self.layouts, self.buttons):
                if button.enabled and layout is not None and button.contains(event.pos):
                    self.start_level(layout)
                    return

    def update(self, dt: float) -> None:
        # Nothing to advance over time; the screen is entirely event driven
        pass

    def draw(self) -> None:
        self.screen.fill("black")

        title_text, title_rect = render_text(
            self.title_font, CUSTOM_SELECT_TITLE, MENU_ENABLED_COLOR, self.title_center
        )
        self.screen.blit(title_text, title_rect)

        if not self.levels:
            self._draw_empty_message(title_rect)

        for button in self.buttons:
            button.draw(self.screen)

    def _draw_empty_message(self, title_rect: pygame.Rect) -> None:
        message, message_rect = render_text(
            self.empty_font,
            CUSTOM_EMPTY_MESSAGE,
            CUSTOM_EMPTY_COLOR,
            (self.screen.get_width() // 2, title_rect.bottom + LEVEL_TITLE_GAP + LEVEL_BOX_SIZE // 2),
        )
        self.screen.blit(message, message_rect)
