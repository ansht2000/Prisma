import pygame
from mirror import Mirror
from table import Table
from laser import Laser

def main():
    # pygame setup
    pygame.init()
    pygame.display.set_caption("Prisma")
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    running = True

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    mirrors = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    Mirror.containers = (updatable, drawable, mirrors)
    Laser.containers = (updatable, drawable, lasers)
    table = Table(screen)
    selected_mirror = None  # The currently selected mirror
    selected_laser = None
    dragging = False        # Whether dragging is active

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                table.resize(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if the click is on the mirror in the table
                mirror_rect_in_table = table.entry_rects.get("mirror")
                laser_rect_in_table = table.entry_rects.get("laser")
                if mirror_rect_in_table and mirror_rect_in_table.collidepoint(event.pos):
                    # Create a new mirror object at the mouse position
                    mouse_x, mouse_y = event.pos
                    new_mirror = Mirror(mouse_x, mouse_y, screen)
                    selected_mirror = new_mirror
                    dragging = True
                else:
                    # Check if any mirror is clicked in the main area
                    for mirror in mirrors:
                        if mirror.rect.collidepoint(event.pos):
                            selected_mirror = mirror
                            dragging = True
                            break
                if laser_rect_in_table and laser_rect_in_table.collidepoint(event.pos):
                    # Create a new mirror object at the mouse position
                    mouse_x, mouse_y = event.pos
                    new_laser = Laser(mouse_x, mouse_y, screen)
                    selected_laser = new_laser
                    dragging = True
                else:
                    # Check if any mirror is clicked in the main area
                    for laser in lasers:
                        if laser.rect.collidepoint(event.pos):
                            selected_laser = laser
                            dragging = True
                            break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                selected_mirror = None
                selected_laser = None

        # Update the position of the selected mirror during dragging
        if dragging and selected_mirror:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            selected_mirror.set_position(mouse_x, mouse_y)
        elif dragging and selected_laser:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            selected_laser.set_position(mouse_x, mouse_y)

        # Fill the screen with a color to wipe away anything from the last frame
        screen.fill("black")

        # Draw the table and other elements
        table.draw()
        for obj in drawable:
            obj.draw()

        for obj in updatable:
            obj.update(table.rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()