import pygame

# Shared color/coordinate aliases -- pygame's own ColorValue/Coordinate types
# live in the private, stub-only pygame._common, so these are kept local
# instead of reaching into that module.
RGBColor = tuple[int, int, int]
Color = str | RGBColor


# renders text into a surface and returns that surface and the rect bounding it
def render_text(
    font: pygame.font.Font,
    text: str,
    color: Color,
    center_position: tuple[float, float],
) -> tuple[pygame.Surface, pygame.Rect]:
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_position)
    return text_surface, text_rect
