from dataclasses import dataclass
from typing import Callable

import pygame

from button import Button
from constants import *
from render_utils import render_text


@dataclass(frozen=True)
class OverlayChoice:
    label: str
    # Takes no arguments: build it as a closure over whatever it needs to act on
    action: Callable[[], None]
    # Listed but unclickable -- drawn dimmed, ignores clicks
    enabled: bool = True


class ChoiceOverlay:
    # A titled panel of buttons drawn on top of a scene, dimming whatever is
    # behind it. The scene that owns one should hand it every event first and
    # draw it last, so it takes priority over the scene underneath.
    def __init__(self, screen: pygame.Surface, title: str, choices: list[OverlayChoice]) -> None:
        self.screen: pygame.Surface = screen
        self.title: str = title
        self.choices: list[OverlayChoice] = choices
        self.title_font: pygame.font.Font = pygame.font.SysFont("Arial", OVERLAY_TITLE_FONT_SIZE)
        self.button_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_BUTTON_FONT_SIZE)
        self.buttons: list[Button] = []
        self.panel: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.title_center: tuple[float, float] = (0, 0)
        self._layout()

    def _layout(self) -> None:
        count = len(self.choices)
        buttons_height = count * MENU_BUTTON_HEIGHT + max(count - 1, 0) * MENU_BUTTON_SPACING
        panel_width = MENU_BUTTON_WIDTH + 2 * OVERLAY_PADDING
        panel_height = (
            OVERLAY_PADDING
            + OVERLAY_TITLE_FONT_SIZE
            + OVERLAY_TITLE_GAP
            + buttons_height
            + OVERLAY_PADDING
        )
        self.panel = pygame.Rect(0, 0, panel_width, panel_height)
        self.panel.center = (self.screen.get_width() // 2, self.screen.get_height() // 2)

        self.title_center = (
            self.panel.centerx,
            self.panel.top + OVERLAY_PADDING + OVERLAY_TITLE_FONT_SIZE // 2,
        )
        buttons_top = self.panel.top + OVERLAY_PADDING + OVERLAY_TITLE_FONT_SIZE + OVERLAY_TITLE_GAP
        self.buttons = [
            Button(
                choice.label,
                pygame.Rect(
                    self.panel.left + OVERLAY_PADDING,
                    buttons_top + index * (MENU_BUTTON_HEIGHT + MENU_BUTTON_SPACING),
                    MENU_BUTTON_WIDTH,
                    MENU_BUTTON_HEIGHT,
                ),
                self.button_font,
                choice.enabled,
            )
            for index, choice in enumerate(self.choices)
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.hovered = button.contains(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for choice, button in zip(self.choices, self.buttons):
                if button.enabled and button.contains(event.pos):
                    choice.action()
                    return

    def draw(self) -> None:
        # Dim the scene underneath so the panel reads as modal
        dim = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, OVERLAY_DIM_ALPHA))
        self.screen.blit(dim, (0, 0))

        pygame.draw.rect(self.screen, OVERLAY_PANEL_FILL, self.panel)
        pygame.draw.rect(self.screen, MENU_ENABLED_COLOR, self.panel, MENU_BORDER_WIDTH)

        title_text, title_rect = render_text(
            self.title_font, self.title, MENU_ENABLED_COLOR, self.title_center
        )
        self.screen.blit(title_text, title_rect)

        for button in self.buttons:
            button.draw(self.screen)
