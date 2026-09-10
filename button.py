import pygame

from constants import *
from render_utils import render_text


class Button:
    # A labelled, clickable box. Knows how to draw itself and whether a point
    # is inside it; it deliberately holds no idea of what clicking it means --
    # that belongs to whatever screen owns the button (see menu.py).
    def __init__(
        self,
        label: str,
        rect: pygame.Rect,
        font: pygame.font.Font,
        enabled: bool = True,
    ) -> None:
        self.label: str = label
        self.rect: pygame.Rect = rect
        self.font: pygame.font.Font = font
        self.enabled: bool = enabled
        self.hovered: bool = False

    def contains(self, pos: tuple[float, float]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface) -> None:
        # Disabled buttons still draw, just dimmed and without the hover fill,
        # so an option can be listed before it is actually built
        fill = MENU_BUTTON_HOVER_FILL if self.hovered and self.enabled else MENU_BUTTON_FILL
        foreground = MENU_ENABLED_COLOR if self.enabled else MENU_DISABLED_COLOR

        pygame.draw.rect(surface, fill, self.rect)
        pygame.draw.rect(surface, foreground, self.rect, MENU_BORDER_WIDTH)

        label_text, label_rect = render_text(
            self.font, self.label, foreground, self.rect.center
        )
        surface.blit(label_text, label_rect)
