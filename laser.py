import pygame
import math

class Laser(pygame.sprite.Sprite):
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
        