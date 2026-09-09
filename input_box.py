import pygame

from constants import *
from render_utils import render_text


class InputBox:
    # A small pop-up that reads a number of degrees and snaps its target to that orientation
    def __init__(self, target, screen, arena_width):
        self.target = target
        self.screen = screen
        self.text = ""
        self.font = pygame.font.SysFont("Arial", INPUT_BOX_FONT_SIZE)
        self.label_font = pygame.font.SysFont("Arial", INPUT_BOX_LABEL_FONT_SIZE)
        self.rect = self._position_near_target(arena_width)

    def _position_near_target(self, arena_width):
        # Sit just above the object, dropping below it when there is no room at the top
        target_rect = self.target.rect
        x = target_rect.centerx - INPUT_BOX_WIDTH // 2
        y = target_rect.top - INPUT_BOX_HEIGHT - INPUT_BOX_MARGIN
        if y < 0:
            y = target_rect.bottom + INPUT_BOX_MARGIN
        # Keep the whole box inside the arena, clear of the table on the right
        x = max(0, min(x, arena_width - INPUT_BOX_WIDTH))
        y = max(0, min(y, self.screen.get_height() - INPUT_BOX_HEIGHT))
        return pygame.Rect(x, y, INPUT_BOX_WIDTH, INPUT_BOX_HEIGHT)

    def handle_event(self, event):
        # Feed the box one event, returns True once it should close
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Clicking off the box commits, same as pressing enter
            if not self.rect.collidepoint(event.pos):
                self.commit()
                return True
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.commit()
                return True
            if event.key == pygame.K_ESCAPE:
                # Back out without touching the object
                return True
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return False
            if len(self.text) < INPUT_BOX_MAX_CHARS and self._is_allowed(event.unicode):
                self.text += event.unicode
            return False

        return False

    def _is_allowed(self, char):
        if char.isdigit():
            return True
        # A minus sign only leads, and only one decimal point
        if char == "-" and self.text == "":
            return True
        return bool(char == "." and "." not in self.text)

    def commit(self):
        try:
            degrees = float(self.text)
        except ValueError:
            # Empty or partial input ("", "-", ".") leaves the object as it was
            return
        self.target.set_orientation(degrees)

    def draw(self):
        pygame.draw.rect(self.screen, (20, 20, 20), self.rect)
        pygame.draw.rect(self.screen, "white", self.rect, 2)

        label_text, label_rect = render_text(
            self.label_font, "Degrees", (180, 180, 180),
            (self.rect.centerx, self.rect.top + INPUT_BOX_LABEL_FONT_SIZE)
        )
        self.screen.blit(label_text, label_rect)

        # The trailing caret makes it obvious the box is taking keystrokes
        entry_text, entry_rect = render_text(
            self.font, self.text + "|", (255, 255, 255),
            (self.rect.centerx, self.rect.bottom - INPUT_BOX_FONT_SIZE)
        )
        self.screen.blit(entry_text, entry_rect)
