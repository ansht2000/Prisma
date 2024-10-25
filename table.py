import pygame
from render_utils import *
from mirror import Mirror
from constants import *

class Table:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.height = screen.get_height()
        self.width = screen.get_width() * 5/6
        # Pre-compute frequently used values
        self.screen_width = screen.get_width()
        self.center_x = (self.width + self.screen_width) // 2
        self.entry_rects = {}
        self.marking_rects = []
        # Initialize entries and positions
        self.entries = [("mirror", Mirror, OBJECT_PADDING)]
        self.rect = pygame.Rect(
            self.width, 0, 
            self.screen_width - self.width, 
            self.height
        )
        
    def draw(self):
        self._draw_table_side()
        self._draw_table_title()
        self._draw_table_markings()
        self._draw_table_objects_and_names()
        
    def _draw_table_side(self):
        pygame.draw.line(
            self.screen, "white", 
            (self.width, 0), 
            (self.width, self.height)
        )

    def _draw_table_title(self):
        title_y = self.screen.get_rect().top + PADDING_TOP
        font = pygame.font.SysFont("Arial", TITLE_FONT_SIZE)
        title_text, title_rect = render_text(
            font, "Objects", (255, 255, 255), 
            (self.center_x, title_y)
        )
        self.entry_rects["title"] = title_rect
        self.screen.blit(title_text, title_rect)

    def _draw_table_markings(self):
        marking_top_y = self.entry_rects["title"].bottom + MARKING_OFFSET
        marking_bottom_y = marking_top_y + 5
        for y in [marking_top_y, marking_bottom_y]:
            marking_rect = pygame.draw.line(
                self.screen, "white", 
                (self.width, y), 
                (self.screen_width, y)
            )
            self.marking_rects.append(marking_rect)

    def _draw_table_objects_and_names(self):
        # Iterate through each entry and draw it
        for name, obj_class, padding in self.entries:
            obj_y = self.marking_rects[-1].bottom + padding
            obj = obj_class(self.center_x, obj_y, self.screen, 100)
            obj_rect = obj.draw()

            font = pygame.font.SysFont("Arial", OBJECT_FONT_SIZE)
            obj_text, obj_text_rect = render_text(
                font, name, (255, 255, 255), 
                (self.center_x, obj_y + 75)
            )
            self.screen.blit(obj_text, obj_text_rect)

            # Merge the object's rects for easier handling
            combined_rect = obj_rect.union(obj_text_rect)
            bottom_line_start = pygame.Vector2(self.width, combined_rect.bottom + 20)
            bottom_line_end = pygame.Vector2(self.screen_width, combined_rect.bottom + 20)
            bottom_line_rect = pygame.draw.line(
                self.screen, "white", 
                bottom_line_start, bottom_line_end
            )
            combined_rect = combined_rect.union(bottom_line_rect)

            # Store the entry rect
            self.entry_rects[name] = combined_rect

    def resize(self, event):
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

        




