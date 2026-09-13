import pygame

from constants import *


class Target:
    # The piece a level's beam has to land on. Deliberately not a Sprite: it
    # never joins the update/draw groups, the level owns it directly.
    #
    # Landing the beam on one is not enough: it has to be held there while the
    # target fills with colour from the bottom up, and only a full target wins
    # the level. Take the beam off and it drains back at the same pace.
    def __init__(self, pos_x: float, pos_y: float, screen: pygame.Surface, size: int = TARGET_SIZE) -> None:
        self.screen: pygame.Surface = screen
        self.pos_x: float = pos_x
        self.pos_y: float = pos_y
        self.size: int = size
        self.rect: pygame.Rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (int(pos_x), int(pos_y))
        # How far along the fill is, from 0 (untouched) to 1 (full)
        self.charge: float = 0.0

    def set_position(self, x: float, y: float) -> None:
        # Same shape as Mirror.set_position/Laser.set_position, so anything
        # that moves a piece around can treat all three alike
        self.pos_x = x
        self.pos_y = y
        self.rect.center = (int(x), int(y))

    def is_hit_by(self, beam_path: list[pygame.Vector2]) -> bool:
        # True when any segment of the beam crosses this target. clipline()
        # returns the clipped segment, or an empty tuple when they never meet.
        for start, end in zip(beam_path, beam_path[1:]):
            if self.rect.clipline(start, end):
                return True
        return False

    def advance(self, dt: float, lit: bool) -> None:
        # Fills while the beam is on it and drains at that same pace when it
        # is not, so taking the beam away briefly costs only what it costs to
        # put back -- a full TARGET_CHARGE_SECONDS of beam is still what fills
        # an empty target
        step = dt / TARGET_CHARGE_SECONDS
        if lit:
            self.charge = min(self.charge + step, 1.0)
        else:
            self.charge = max(self.charge - step, 0.0)

    @property
    def is_charged(self) -> bool:
        return self.charge >= 1.0

    def draw(self) -> None:
        self._draw_in(TARGET_COLOR)
        if self.charge <= 0:
            return

        # The same target again in the fill colour, but only the bottom slice
        # of it, so the colour climbs as the charge does
        filled_height = round(self.rect.height * self.charge)
        rising = pygame.Rect(
            self.rect.left,
            self.rect.bottom - filled_height,
            self.rect.width,
            filled_height,
        )
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(rising)
        self._draw_in(TARGET_CHARGE_COLOR)
        self.screen.set_clip(previous_clip)

    def _draw_in(self, color: tuple[int, int, int]) -> None:
        for band in self._ring_bands() + [self._inner_block()]:
            pygame.draw.rect(self.screen, color, band)

    def _ring_bands(self) -> list[pygame.Rect]:
        # The outer ring, as four filled bars rather than one rect asked for a
        # border width. Drawn the latter way, pygame fills the rect solid once
        # the clip above has narrowed it to about twice that width -- which
        # painted the space inside the ring as the charge rose past it.
        edge = TARGET_BORDER_WIDTH
        return [
            pygame.Rect(self.rect.left, self.rect.top, self.rect.width, edge),
            pygame.Rect(self.rect.left, self.rect.bottom - edge, self.rect.width, edge),
            pygame.Rect(self.rect.left, self.rect.top, edge, self.rect.height),
            pygame.Rect(self.rect.right - edge, self.rect.top, edge, self.rect.height),
        ]

    def _inner_block(self) -> pygame.Rect:
        # So the target still reads as solid from a distance
        return self.rect.inflate(-self.size // 2, -self.size // 2)
