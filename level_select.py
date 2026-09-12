import pygame

from button import Button
from constants import *
from levels import LEVELS, LevelLayout
from render_utils import render_text
from scene import Scene


def layout_boxes(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    count: int,
    box_width: int = LEVEL_BOX_SIZE,
    box_height: int = LEVEL_BOX_SIZE,
) -> tuple[list[pygame.Rect], tuple[float, float]]:
    """Lays a screenful of level boxes out under a heading.

    The heading sits at the top of the screen and the first row of boxes
    starts just below it, filling rightwards from the left margin and
    wrapping down a row when they run out of width. Shared so the custom
    level screen and the built-in one are laid out by the same rules.

    Returns the box rects, in order, and where the heading should be centered.
    """
    width = screen.get_width()
    title_height = title_font.get_height()
    title_center = (width // 2, LEVEL_BOX_MARGIN + title_height // 2)

    top = LEVEL_BOX_MARGIN + title_height + LEVEL_TITLE_GAP
    step_x = box_width + LEVEL_BOX_SPACING
    step_y = box_height + LEVEL_BOX_SPACING
    usable = max(width - 2 * LEVEL_BOX_MARGIN, box_width)
    per_row = max(usable // step_x, 1)

    rects = [
        pygame.Rect(
            LEVEL_BOX_MARGIN + (index % per_row) * step_x,
            top + (index // per_row) * step_y,
            box_width,
            box_height,
        )
        for index in range(count)
    ]
    return rects, title_center


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
        rects, self.title_center = layout_boxes(
            self.screen, self.title_font, len(self.levels)
        )
        self.buttons = [
            Button(str(level.number), rect, self.box_font)
            for level, rect in zip(self.levels, rects)
        ]

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
