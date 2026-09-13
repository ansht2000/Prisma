from typing import Callable

import pygame
from render_utils import *
from mirror import Mirror
from laser import Laser
from target import Target
from wall import Wall
from constants import *

TableEntry = Mirror | Laser | Target | Wall
# Builds one sample piece for the table to show, at the given position. The
# table only draws these -- the scene decides what a drag off one produces.
EntryFactory = Callable[[float, float, pygame.Surface], TableEntry]
# A row of the table: the name under the piece, how to build it, and the gap
# above it.
TableRow = tuple[str, EntryFactory, int]


# Samples are built at the size a piece is actually drawn at, and are shared
# between the screens, so the same object looks the same wherever it is listed.


def _mirror(x: float, y: float, screen: pygame.Surface) -> TableEntry:
    return Mirror(x, y, screen, length=MIRROR_LENGTH, add_to_groups=False)


def _laser(x: float, y: float, screen: pygame.Surface) -> TableEntry:
    return Laser(x, y, screen, length=LASER_LENGTH, add_to_groups=False)


def _target(x: float, y: float, screen: pygame.Surface) -> TableEntry:
    return Target(x, y, screen)


def _wall(x: float, y: float, screen: pygame.Surface) -> TableEntry:
    return Wall(x, y, screen, length=WALL_LENGTH, add_to_groups=False)


# What the sandbox offers: everything free play can do something with. It has
# no target, since it has nothing to win.
SANDBOX_ENTRIES: list[TableRow] = [
    ("mirror", _mirror, OBJECT_PADDING),
    ("laser", _laser, OBJECT_PADDING),
    ("wall", _wall, OBJECT_PADDING),
]

# What the level editor offers: the same pieces, drawn the same way, plus the
# target a level has to be aimed at.
EDITOR_ENTRIES: list[TableRow] = [
    ("mirror", _mirror, OBJECT_PADDING),
    ("laser", _laser, OBJECT_PADDING),
    ("target", _target, OBJECT_PADDING),
    ("wall", _wall, OBJECT_PADDING),
]


class Table:
    def __init__(self, screen: pygame.Surface, entries: list[TableRow] | None = None) -> None:
        self.screen: pygame.Surface = screen
        self.height: float = screen.get_height()
        self.width: float = screen.get_width() * 5/6
        # Pre-compute frequently used values
        self.screen_width: float = screen.get_width()
        self.center_x: float = (self.width + self.screen_width) // 2
        self.entry_rects: dict[str, pygame.Rect] = {}
        self.marking_rects: list[pygame.Rect] = []
        # Injectable so the level editor can offer a different set of pieces
        # than the sandbox without a second copy of this screen furniture
        self.entries: list[TableRow] = SANDBOX_ENTRIES if entries is None else entries
        self.rect: pygame.Rect = pygame.Rect(
            self.width, 0,
            self.screen_width - self.width,
            self.height
        )

    def draw(self) -> None:
        self._draw_table_side()
        self._draw_table_title()
        self._draw_table_markings()
        self._draw_table_objects_and_names()

    def _draw_table_side(self) -> None:
        pygame.draw.line(
            self.screen, "white",
            (self.width, 0),
            (self.width, self.height)
        )

    def _draw_table_title(self) -> None:
        title_y = self.screen.get_rect().top + PADDING_TOP
        font = pygame.font.SysFont("Arial", TITLE_FONT_SIZE)
        title_text, title_rect = render_text(
            font, "Objects", (255, 255, 255),
            (self.center_x, title_y)
        )
        self.entry_rects["title"] = title_rect
        self.screen.blit(title_text, title_rect)

    def _draw_table_markings(self) -> None:
        # Rebuilt from scratch every frame: the rects below are laid out
        # relative to the last one in this list, so a stale frame's worth
        # would both mislay them and grow the list without bound
        self.marking_rects = []
        marking_top_y = self.entry_rects["title"].bottom + MARKING_OFFSET
        marking_bottom_y = marking_top_y + 5
        for y in [marking_top_y, marking_bottom_y]:
            marking_rect = pygame.draw.line(
                self.screen, "white",
                (self.width, y),
                (self.screen_width, y)
            )
            self.marking_rects.append(marking_rect)

    def _draw_table_objects_and_names(self) -> None:
        # Iterate through each entry and draw it
        for name, make_entry, padding in self.entries:
            obj_y = self.marking_rects[-1].bottom + padding
            obj = make_entry(self.center_x, obj_y, self.screen)
            obj.draw()
            obj_rect = obj.rect
            assert obj_rect is not None  # drawing a piece is what sizes its rect

            # The name sits just under whatever was drawn, rather than a
            # fixed distance below its middle: entries then take only the room
            # their object needs, and every object fits on the one page
            font = pygame.font.SysFont("Arial", OBJECT_FONT_SIZE)
            obj_text, obj_text_rect = render_text(
                font, name, (255, 255, 255),
                (self.center_x, obj_rect.bottom + OBJECT_LABEL_GAP)
            )
            self.screen.blit(obj_text, obj_text_rect)

            # Merge the object's rects for easier handling
            combined_rect = obj_rect.union(obj_text_rect)
            divider_y = combined_rect.bottom + OBJECT_DIVIDER_GAP
            bottom_line_start = pygame.Vector2(self.width, divider_y)
            bottom_line_end = pygame.Vector2(self.screen_width, divider_y)
            bottom_line_rect = pygame.draw.line(
                self.screen, "white",
                bottom_line_start, bottom_line_end
            )
            combined_rect = combined_rect.union(bottom_line_rect)

            # Store the entry rect
            self.entry_rects[name] = combined_rect
            self.marking_rects.append(combined_rect)

    def resize(self, event: pygame.event.Event) -> None:
        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        self.height = self.screen.get_height()
        self.width = self.screen.get_width() * 5/6
        # Pre-compute frequently used values
        self.screen_width = self.screen.get_width()
        self.center_x = (self.width + self.screen_width) // 2
        self.rect = pygame.Rect(
            self.width, 0,
            self.screen_width - self.width,
            self.height
        )
