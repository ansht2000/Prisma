import pygame
from mirror import Mirror
from table import Table
from laser import Laser
from laserbeam import LaserBeam
from constants import *

def main():
    # pygame setup
    pygame.init()
    pygame.display.set_caption("Prisma")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT ), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    running = True
    dt = 0

    # Make groups for all the relevant collections of objects
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    deletable = pygame.sprite.Group() # Objects that can be dragged to the table and deleted
    mirrors = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    laser_beams = pygame.sprite.Group()
    Mirror.containers = (updatable, drawable, mirrors, deletable)
    Laser.containers = (updatable, drawable, lasers, deletable)
    LaserBeam.containers = (updatable, drawable, laser_beams)
    table = Table(screen)
    # The currently selected mirror
    selected_mirror = None
    selected_laser = None
    # Whether dragging is active
    dragging = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                table.resize(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mirror_rect_in_table = table.entry_rects.get("mirror")
                laser_rect_in_table = table.entry_rects.get("laser")
                # Check if the click is on the mirror in the table
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
                # Check if the click is on the laser in the table
                if laser_rect_in_table and laser_rect_in_table.collidepoint(event.pos):
                    # Create a new laser object at the mouse position
                    mouse_x, mouse_y = event.pos
                    new_laser = Laser(mouse_x, mouse_y, screen)
                    selected_laser = new_laser
                    dragging = True
                else:
                    # Check if any laser is clicked in the main area
                    for laser in lasers:
                        if laser.rect.collidepoint(event.pos) and not laser.laser_on:
                            selected_laser = laser
                            dragging = True
                            break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                selected_mirror = None
                selected_laser = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                for laser in lasers:
                    if laser.rect.collidepoint(event.pos):
                        if not laser.laser_on:
                            laser.laser_on = True
                            laser_start = laser.get_laser_point()
                            laser.laser_beam = LaserBeam(laser_start, screen, laser.orientation, mirrors)
                        else:
                            laser.laser_on = False
                            laser.laser_beam.kill()
                            laser.laser_beam = None

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
            obj.update(dt)

        for obj in deletable:
            obj.check_delete(table.rect)

        pygame.display.flip()
        dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()