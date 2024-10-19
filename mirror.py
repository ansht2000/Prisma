import pygame
import math

class Mirror(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, length=10, orientation=45):
        super().__init__()
        self.curved = False
        # the x and y positions define the center of the line
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.length = length
        self.orientation = orientation

    def draw(self, screen):
        radians = (math.pi * self.orientation) / 180
        start_x = self.pos_x - (self.length / 2) * math.cos(radians)
        start_y = self.pos_y + (self.length / 2) * math.sin(radians)
        start_pos = pygame.Vector2(start_x, start_y)
        end_pos = pygame.Vector2(start_x + self.length * math.cos(radians), start_y - self.length * math.sin(radians))
        return pygame.draw.line(screen, "white", start_pos, end_pos)

    

    