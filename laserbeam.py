import pygame
import math

class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, start_point, screen, orientation):
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.screen = screen
        self.start_pos = start_point
        self.orientation = orientation

    def draw(self):
        radians = (math.pi * self.orientation) / 180
        end_pos = pygame.Vector2(
            self.start_pos.x + 100 * math.cos(radians), 
            self.start_pos.y - 100 * math.sin(radians)
        )
        pygame.draw.line(
            self.screen,
            "red",
            self.start_pos,
            end_pos,
            10
        )
