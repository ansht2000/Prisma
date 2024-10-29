import pygame
import math

class Laser(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, screen, length=100, orientation=180, add_to_groups = True):
        if add_to_groups and hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen = screen
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.length = length
        self.width = 50
        self.orientation = orientation
        self.rect = None
        self.dragging = False

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
        # pygame.draw.rect(self.screen, "white", self.rect)
        return self.rect

    def set_position(self, x, y):
        self.pos_x = x
        self.pos_y = y 

    def update(self, table_rect):
        if self.rect.colliderect(table_rect) and not pygame.mouse.get_pressed()[0]:
            self.kill()
