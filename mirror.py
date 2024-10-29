import pygame
import math

class Mirror(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, screen, length=100, orientation=45, add_to_groups = True):
        if add_to_groups and hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen = screen
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.start_pos = None
        self.end_pos = None
        self.length = length
        self.orientation = orientation
        self.rect = None
        self.dragging = False

    def draw(self):
        radians = (math.pi * self.orientation) / 180
        start_x = self.pos_x - (self.length / 2) * math.cos(radians)
        start_y = self.pos_y + (self.length / 2) * math.sin(radians)
        start_pos = pygame.Vector2(start_x, start_y)
        end_pos = pygame.Vector2(
            start_x + self.length * math.cos(radians), 
            start_y - self.length * math.sin(radians)
        )
        self.start_pos = start_pos
        self.end_pos = end_pos

        # Create a larger hitbox around the line
        padding = 10  # Padding around the line to create a larger hitbox
        self.rect = pygame.Rect(
            min(start_x, end_pos.x) - padding, 
            min(start_y, end_pos.y) - padding, 
            abs(start_x - end_pos.x) + padding, 
            abs(start_y - end_pos.y) + padding
        )

        # Draw the line and the hitbox for debugging
        pygame.draw.line(self.screen, "white", start_pos, end_pos)
        return self.rect

    def set_position(self, x, y):
        self.pos_x = x
        self.pos_y = y

    def update(self, table_rect):
        if self.rect.colliderect(table_rect) and not pygame.mouse.get_pressed()[0]:
            self.kill()
        
        
