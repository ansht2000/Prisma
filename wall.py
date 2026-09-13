import math
from typing import ClassVar

import pygame

from constants import *
from controls import turn_with_keys


class Wall(pygame.sprite.Sprite):
    # An obstacle: the same line a mirror is, drawn thicker and grey, that a
    # beam stops at instead of bouncing off (see laserbeam.py).

    # Declared, not assigned: SandboxScene sets this class attribute, and the
    # hasattr() check in __init__ relies on it being genuinely absent until
    # then, so this must stay a bare annotation.
    containers: ClassVar[tuple[pygame.sprite.Group, ...]]

    def __init__(
        self,
        pos_x: float,
        pos_y: float,
        screen: pygame.Surface,
        length: float = MIRROR_DEFAULT_SIZE,
        # Upright by default: a laser fires to the right unless it is turned,
        # so a wall dropped in its way blocks it rather than lying along it
        orientation: float = 90,
        add_to_groups: bool = True,
    ) -> None:
        if add_to_groups and hasattr(self, "containers"):
            super().__init__(*self.containers)
        else:
            super().__init__()
        self.screen: pygame.Surface = screen
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.start_pos: pygame.Vector2 | None = None
        self.end_pos: pygame.Vector2 | None = None
        self.length: float = length
        self.orientation: float = orientation % 360
        self.rect: pygame.Rect | None = None

    def draw(self) -> pygame.Rect:
        radians = (math.pi * self.orientation) / 180
        start_x = self.pos_x - (self.length / 2) * math.cos(radians)
        start_y = self.pos_y + (self.length / 2) * math.sin(radians)
        start_pos = pygame.Vector2(start_x, start_y)
        end_pos = pygame.Vector2(
            start_x + self.length * math.cos(radians),
            start_y - self.length * math.sin(radians),
        )
        self.start_pos = start_pos
        self.end_pos = end_pos

        # A hitbox around the line, as Mirror does, so the editor can pick a
        # wall up by clicking anywhere near it
        padding = WALL_WIDTH
        self.rect = pygame.Rect(
            min(start_x, end_pos.x) - padding,
            min(start_y, end_pos.y) - padding,
            abs(start_x - end_pos.x) + 2 * padding,
            abs(start_y - end_pos.y) + 2 * padding,
        )

        pygame.draw.line(self.screen, WALL_COLOR, start_pos, end_pos, WALL_WIDTH)
        return self.rect

    def set_position(self, x: float, y: float) -> None:
        self.pos_x = x
        self.pos_y = y

    def check_delete(self, table_rect: pygame.Rect) -> None:
        assert self.rect is not None  # draw() runs every frame before this is called
        if self.rect.colliderect(table_rect) and not pygame.mouse.get_pressed()[0]:
            self.kill()

    def rotate(self, dt: float) -> None:
        self.orientation += ROTATION_SPEED * dt
        self.orientation %= 360

    def set_orientation(self, degrees: float) -> None:
        self.orientation = degrees % 360

    def update(self, dt: float) -> None:
        assert self.rect is not None  # draw() runs every frame before this is called
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_x, mouse_y):
            turn_with_keys(self, dt)
