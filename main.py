import pygame
from mirror import Mirror
from table import Table
from constants import *

def main():
    # pygame setup
    pygame.init()
    pygame.display.set_caption("Prisma")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    running = True
    dt = 0

    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    Mirror.containers = (updatable, drawable)

    # Initialize table and mirror objects
    table = Table(screen)
    dragging_entry = False  # Track dragging from table
    dragging_mirror = False  # Track dragging of mirrors
    temp_mirror = None  # Temporary mirror during drag

    while running:
        # Poll for events in the main loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if clicking on the mirror entry in the table
                if table.entry_rects["mirror"].collidepoint(event.pos):
                    dragging_entry = True  # Start dragging from table
                    temp_mirror = Mirror(event.pos[0], event.pos[1], screen, MIRROR_DEFAULT_SIZE)
                else:
                    # Check if clicking on an existing mirror
                    for mirror in drawable:
                        if mirror.rect.collidepoint(event.pos):
                            dragging_mirror = True
                            temp_mirror = mirror
                            break

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # Release the dragging state
                if dragging_entry and temp_mirror:
                    # Add the temporary mirror to the groups
                    drawable.add(temp_mirror)
                    updatable.add(temp_mirror)
                    temp_mirror = None
                    dragging_entry = False 

                if dragging_mirror:
                    dragging_mirror = False
                    temp_mirror = None

            if event.type == pygame.VIDEORESIZE:
                table.resize(event)

        # Update the position of the dragging mirror or temporary mirror
        if dragging_entry or dragging_mirror:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if temp_mirror:
                temp_mirror.set_position(mouse_x, mouse_y)

        # Fill the screen with a color to wipe away anything from the last frame
        screen.fill("black")

        # Render game here
        table.draw()
        for obj in drawable:
            obj.draw()

        for obj in updatable:
            obj.update(table.rect)

        # Flip display to show the work done on the screen
        pygame.display.flip()

        # Limits the FPS to 60
        dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()
