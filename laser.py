import pygame
import math
from constants import ROTATION_SPEED

class Laser(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, screen, length=100, orientation=0, add_to_groups = True):
        if add_to_groups and hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen = screen
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.length = length
        self.width = 50
        self.orientation = orientation % 360
        self.top_left = None
        self.top_right = None
        self.bottom_left = None
        self.bottom_right = None
        self.rect = None
        self.dragging = False
        self.laser_on = False
        self.laser_beam = None

    def draw(self):
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

        # Draw the laser
        pygame.draw.polygon(self.screen, "white", [top_left, top_right, bottom_right, bottom_left])
        return self.rect

    def set_position(self, x, y):
        self.pos_x = x
        self.pos_y = y

    def check_delete(self, table_rect):
        if self.rect.colliderect(table_rect) and not pygame.mouse.get_pressed()[0]:
            if self.laser_beam:
                self.laser_beam.kill()
            self.kill()

    def rotate(self, dt):
        self.orientation += ROTATION_SPEED * dt
        self.orientation %= 360

    def update(self, dt):
        # This is here for the meantime since the laser beam does not move with the laser
        # Will remove when laser beam moving logic is correctly implemented
        if self.laser_on:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_x, mouse_y):
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                self.rotate(dt)
            if keys[pygame.K_d]:
                self.rotate(-dt)

    def get_laser_point(self):
        laser_x = (self.top_right.x + self.bottom_right.x) // 2
        laser_y = (self.top_right.y + self.bottom_right.y) // 2
        return pygame.Vector2(laser_x, laser_y)
