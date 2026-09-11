import pygame

from constants import *


class Target:
    # The piece a level's beam has to land on. Deliberately not a Sprite: it
    # never joins the update/draw groups, the level owns it directly.
    def __init__(self, pos_x: float, pos_y: float, screen: pygame.Surface, size: int = TARGET_SIZE) -> None:
        self.screen: pygame.Surface = screen
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.size: int = size
        self.rect: pygame.Rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (int(pos_x), int(pos_y))

    def is_hit_by(self, beam_path: list[pygame.Vector2]) -> bool:
        # True when any segment of the beam crosses this target. clipline()
        # returns the clipped segment, or an empty tuple when they never meet.
        for start, end in zip(beam_path, beam_path[1:]):
            if self.rect.clipline(start, end):
                return True
        return False

    def draw(self, hit: bool = False) -> None:
        color = TARGET_HIT_COLOR if hit else TARGET_COLOR
        pygame.draw.rect(self.screen, color, self.rect, 4)
        # An inner block so the target still reads as solid from a distance
        inner = self.rect.inflate(-self.size // 2, -self.size // 2)
        pygame.draw.rect(self.screen, color, inner)
