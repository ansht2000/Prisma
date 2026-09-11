import pygame

from button import Button
from constants import *
from levels import LEVELS, LevelLayout
from render_utils import render_text
from scene import Scene


class LevelSelectScene(Scene):
    # Grid of level boxes, one per entry in LEVELS. Escape backs out to the
    # menu; clicking a box starts that level.
    def __init__(self, screen: pygame.Surface, levels: list[LevelLayout] | None = None) -> None:
        super().__init__(screen)
        # Injectable so a test (or a future level pack) can supply its own set
        self.levels: list[LevelLayout] = LEVELS if levels is None else levels
        self.title_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_TITLE_FONT_SIZE)
        self.box_font: pygame.font.Font = pygame.font.SysFont("Arial", LEVEL_BOX_FONT_SIZE)
        self.buttons: list[Button] = []
        self.title_center: tuple[float, float] = (0, 0)
        self._layout()

    def _layout(self) -> None:
        # Boxes are anchored to the top-left corner: level 1 sits in the
        # corner and later levels fill rightwards, wrapping down a row when
        # they run out of width. Change this one method to re-arrange them.
        width = self.screen.get_width()
        step = LEVEL_BOX_SIZE + LEVEL_BOX_SPACING
        usable = max(width - 2 * LEVEL_BOX_MARGIN, LEVEL_BOX_SIZE)
        per_row = max(usable // step, 1)

        self.buttons = []
        for index, level in enumerate(self.levels):
            column = index % per_row
            row = index // per_row
            rect = pygame.Rect(
                LEVEL_BOX_MARGIN + column * step,
                LEVEL_BOX_MARGIN + row * step,
                LEVEL_BOX_SIZE,
                LEVEL_BOX_SIZE,
            )
            self.buttons.append(Button(str(level.number), rect, self.box_font))

        self.title_center = (width // 2, LEVEL_BOX_MARGIN + MENU_TITLE_FONT_SIZE // 2)

    def start_level(self, layout: LevelLayout) -> None:
        from level import LevelScene  # local import: LevelScene navigates back here

        self.go_to(LevelScene(self.screen, layout))

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
            for level, button in zip(self.levels, self.buttons):
                if button.enabled and button.contains(event.pos):
                    self.start_level(level)
                    return

    def update(self, dt: float) -> None:
        # Nothing to advance over time; the screen is entirely event driven
        pass

    def draw(self) -> None:
        self.screen.fill("black")

        title_text, title_rect = render_text(
            self.title_font, LEVEL_SELECT_TITLE, MENU_ENABLED_COLOR, self.title_center
        )
        self.screen.blit(title_text, title_rect)

        for button in self.buttons:
            button.draw(self.screen)
