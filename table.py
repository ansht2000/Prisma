import pygame
from render_utils import *
from mirror import Mirror

# this class represents a table of available objects to choose from
class Table:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.height = screen.get_height()
        # sets the table to take up 1/6 of the screen
        self.width = screen.get_width() * 5/6
        # dictionary of entries in the table and their corresponding rects
        self.entry_rects = {}
        # list of marking rects in the table
        self.marking_rects = []

    def draw(self):
        self._draw_table_side()
        self._draw_table_title()
        self._draw_table_markings()
        self._draw_table_objects_and_names()
        
    def _draw_table_side(self):
        table_border_start = pygame.Vector2(self.width, 0)
        table_border_end = pygame.Vector2(self.width, self.height)
        pygame.draw.line(self.screen, "white", table_border_start, table_border_end)

    def _draw_table_title(self):
        # using a magic number to set the distance of the title away from the top of the screen
        title_height = self.screen.get_rect().top + 30
        title_center = (self.width + self.screen.get_width()) // 2
        font = pygame.font.SysFont("Arial", 36)
        title_text, title_rect = render_text(font, "Objects", (255, 255, 255), (title_center, title_height))
        self.entry_rects["title"] = title_rect
        self.screen.blit(title_text, title_rect)

    def _draw_table_markings(self):
        double_marking_top_height = self.entry_rects["title"].bottom + 10
        double_marking_bottom_height = double_marking_top_height + 5
        double_marking_top_start = pygame.Vector2(self.width, double_marking_top_height)
        double_marking_top_end = pygame.Vector2(self.screen.get_width(), double_marking_top_height)
        double_marking_bottom_start = pygame.Vector2(self.width, double_marking_bottom_height)
        double_marking_bottom_end = pygame.Vector2(self.screen.get_width(), double_marking_bottom_height)
        pygame.draw.line(self.screen, "white", double_marking_top_start, double_marking_top_end)
        bottom_marking_rect = pygame.draw.line(self.screen, "white", double_marking_bottom_start, double_marking_bottom_end)
        self.marking_rects.append(bottom_marking_rect)

    def _draw_table_objects_and_names(self):
        # draw the mirror object as the first entry in the table
        mirror_x = (self.width + self.screen.get_width()) // 2
        mirror_y = self.marking_rects[0].bottom + 60
        mirror = Mirror(mirror_x, mirror_y, 100)
        mirror_rect = mirror.draw(self.screen)
        font = pygame.font.SysFont("Arial", 24)
        mirror_text, mirror_text_rect = render_text(font, "Mirror", (255, 255, 255), (mirror_x, mirror_y + 75))
        # convert the mirror rect and mirror text rect into one rect
        mirror_rect = mirror_rect.union(mirror_text_rect)
        self.screen.blit(mirror_text, mirror_text_rect)
        mirror_bottom_line_start = pygame.Vector2(self.width, mirror_rect.bottom + 20)
        mirror_bottom_line_end = pygame.Vector2(self.screen.get_width(), mirror_rect.bottom + 20)
        mirror_bottom_line_rect = pygame.draw.line(self.screen, "white", mirror_bottom_line_start, mirror_bottom_line_end)
        mirror_rect = mirror_rect.union(mirror_bottom_line_rect)
        self.entry_rects["mirror"] = mirror_rect
        




