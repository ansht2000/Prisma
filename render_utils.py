import pygame

# renders text into a surface and returns that surface and the rect bounding it
def render_text(font, text, color, center_position):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_position)
    return text_surface, text_rect