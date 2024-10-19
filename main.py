import pygame
from mirror import Mirror
from table import Table

def main():
    # pygame setup
    pygame.init()
    pygame.display.set_caption("Prisma")
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running  = True
    dt = 0

    while running:
        # poll for events
        # pygame.QUIT represents the user pressing X to close the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # fill the screen with a color to wipe away anything from the last frame
        screen.fill("black")

        # Render game here
        mirror = Mirror(screen.get_width() / 2, screen.get_height() / 2, 100)
        mirror_2 = Mirror(screen.get_width() / 2 + 50, screen.get_height() / 2 + 50, 100, 180)
        mirror.draw(screen)
        mirror_2.draw(screen)
        table = Table(screen)
        table.draw()

        # flip() display to show the work done on the screen
        pygame.display.flip()

        # Limits the FPS to 60
        dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()