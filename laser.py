import math
from typing import TYPE_CHECKING, ClassVar

import pygame

from constants import ROTATION_SPEED
from controls import turn_with_keys

if TYPE_CHECKING:
    from laserbeam import LaserBeam


class Laser(pygame.sprite.Sprite):
    # Declared, not assigned: main() sets this class attribute on startup, and
    # the hasattr() check in __init__ relies on it being genuinely absent
    # until then, so this must stay a bare annotation.
    containers: ClassVar[tuple[pygame.sprite.Group, ...]]

    def __init__(
        self,
        pos_x: float,
        pos_y: float,
        screen: pygame.Surface,
        length: float = 100,
        orientation: float = 0,
        add_to_groups: bool = True,
    ) -> None:
        if add_to_groups and hasattr(self, "containers"):
            super().__init__(*self.containers)
        else:
            super().__init__()
        self.screen: pygame.Surface = screen
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.length: float = length
        self.width: float = 50
        self.orientation: float = orientation % 360
        self.top_left: pygame.Vector2 | None = None
        self.top_right: pygame.Vector2 | None = None
        self.bottom_left: pygame.Vector2 | None = None
        self.bottom_right: pygame.Vector2 | None = None
        self.rect: pygame.Rect | None = None
        self.dragging: bool = False
        self.laser_on: bool = False
        self.laser_beam: LaserBeam | None = None

    def _compute_corners(self) -> pygame.Rect:
        radians = math.radians(self.orientation)
        dir_x = math.cos(radians)
        dir_y = -math.sin(radians)  # Invert the y-component
        perp_x = -dir_y
        perp_y = dir_x

        half_length = self.length / 2
        half_width = self.width / 2

        half_length_x = dir_x * half_length
        half_length_y = dir_y * half_length
        half_width_x = perp_x * half_width
        half_width_y = perp_y * half_width

        # Compute the four corners
        top_left = pygame.Vector2(self.pos_x - half_length_x + half_width_x, self.pos_y - half_length_y + half_width_y)
        top_right = pygame.Vector2(self.pos_x + half_length_x + half_width_x, self.pos_y + half_length_y + half_width_y)
        bottom_left = pygame.Vector2(self.pos_x - half_length_x - half_width_x, self.pos_y - half_length_y - half_width_y)
        bottom_right = pygame.Vector2(self.pos_x + half_length_x - half_width_x, self.pos_y + half_length_y - half_width_y)
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right

        # Put all x and y coords of the corners into a list to use for the rect
        x_coords = [top_left.x, top_right.x, bottom_left.x, bottom_right.x]
        y_coords = [top_left.y, top_right.y, bottom_left.y, bottom_right.y]

        # Create a rect bounding the laser object
        self.rect = pygame.Rect(
            min(x_coords),
            min(y_coords),
            max(x_coords) - min(x_coords),
            max(y_coords) - min(y_coords)
        )

        return self.rect

    def draw(self) -> pygame.Rect:
        # Corners are recomputed every frame so the laser follows drags and rotations
        self._compute_corners()
        assert self.top_left is not None
        assert self.top_right is not None
        assert self.bottom_left is not None
        assert self.bottom_right is not None
        pygame.draw.polygon(
            self.screen, "white",
            [self.top_left, self.top_right, self.bottom_right, self.bottom_left]
        )
        assert self.rect is not None
        return self.rect

    def set_position(self, x: float, y: float) -> None:
        self.pos_x = x
        self.pos_y = y

    def check_delete(self, table_rect: pygame.Rect) -> None:
        assert self.rect is not None  # _compute_corners() runs every frame before this is called
        if self.rect.colliderect(table_rect) and not pygame.mouse.get_pressed()[0]:
            if self.laser_beam:
                self.laser_beam.kill()
            self.kill()

    def rotate(self, dt: float) -> None:
        self.orientation += ROTATION_SPEED * dt
        self.orientation %= 360
        if self.laser_on:
            assert self.laser_beam is not None
            self.laser_beam.start_pos = self.get_laser_point()
            self.laser_beam.orientation = self.orientation

    def set_orientation(self, degrees: float) -> None:
        self.orientation = degrees % 360
        # get_laser_point() reads the corners, so refresh them before moving the beam
        self._compute_corners()
        if self.laser_on and self.laser_beam:
            self.laser_beam.start_pos = self.get_laser_point()
            self.laser_beam.orientation = self.orientation

    def update(self, dt: float) -> None:
        assert self.rect is not None  # _compute_corners() runs every frame before this is called
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_x, mouse_y):
            turn_with_keys(self, dt)

    def get_laser_point(self) -> pygame.Vector2:
        assert self.top_right is not None
        assert self.bottom_right is not None
        laser_x = (self.top_right.x + self.bottom_right.x) // 2
        laser_y = (self.top_right.y + self.bottom_right.y) // 2
        return pygame.Vector2(laser_x, laser_y)
