import pygame

from constants import *
from input_box import InputBox
from laser import Laser
from laserbeam import LaserBeam
from mirror import Mirror
from table import Table


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
    # The open degree-entry box, if any
    input_box = None
    # Where the left button went down, and which existing object it landed on, so
    # that a click can be told apart from a drag once the button comes back up
    press_pos = None
    click_target = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == pygame.VIDEORESIZE:
                table.resize(event)
                continue

            # An open degree box swallows every other interaction, so the click
            # that dismisses it cannot also grab the object underneath
            if input_box is not None:
                if input_box.handle_event(event):
                    input_box = None
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                press_pos = event.pos
                click_target = None
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
                            click_target = mirror
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
                        if laser.rect.collidepoint(event.pos):
                            selected_laser = laser
                            click_target = laser
                            dragging = True
                            break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # A press and release that barely moved is a click, not a drag, and
                # opens the degree box on the object it landed on. Objects just
                # created from the table are excluded, they are being dragged out.
                if click_target is not None and press_pos is not None:
                    moved_x = abs(event.pos[0] - press_pos[0])
                    moved_y = abs(event.pos[1] - press_pos[1])
                    if moved_x <= CLICK_MOVE_THRESHOLD and moved_y <= CLICK_MOVE_THRESHOLD:
                        input_box = InputBox(click_target, screen, table.width)
                dragging = False
                selected_mirror = None
                selected_laser = None
                press_pos = None
                click_target = None
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
        if input_box is None:
            if dragging and selected_mirror:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                selected_mirror.set_position(mouse_x, mouse_y)
            elif dragging and selected_laser:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                selected_laser.set_position(mouse_x, mouse_y)
                if selected_laser.laser_beam:
                    selected_laser.laser_beam.start_pos = selected_laser.get_laser_point()

        # Fill the screen with a color to wipe away anything from the last frame
        screen.fill("black")

        # Draw the table and other elements
        table.draw()
        for obj in drawable:
            obj.draw()

        if input_box is None:
            for obj in updatable:
                obj.update(dt)

            for obj in deletable:
                obj.check_delete(table.rect)
        else:
            # Beams keep tracking their mirrors, but the A/D rotation keys are
            # suspended so typing into the box cannot also spin the object
            for beam in laser_beams:
                beam.update(dt)
            input_box.draw()

        pygame.display.flip()
        dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == "__main__":
    main()
