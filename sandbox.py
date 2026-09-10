import pygame

from constants import *
from input_box import InputBox, Orientable
from laser import Laser
from laserbeam import LaserBeam
from mirror import Mirror
from scene import Scene
from table import Table


class SandboxScene(Scene):
    # Free-play mode: drag mirrors and lasers off the table, aim them, and
    # switch beams on. This is the behaviour the app used to boot straight into.
    def __init__(self, screen: pygame.Surface) -> None:
        super().__init__(screen)

        # Make groups for all the relevant collections of objects
        self.updatable: pygame.sprite.Group = pygame.sprite.Group()
        self.drawable: pygame.sprite.Group = pygame.sprite.Group()
        self.deletable: pygame.sprite.Group = pygame.sprite.Group()  # Objects that can be dragged to the table and deleted
        self.mirrors: pygame.sprite.Group = pygame.sprite.Group()
        self.lasers: pygame.sprite.Group = pygame.sprite.Group()
        self.laser_beams: pygame.sprite.Group = pygame.sprite.Group()
        Mirror.containers = (self.updatable, self.drawable, self.mirrors, self.deletable)
        Laser.containers = (self.updatable, self.drawable, self.lasers, self.deletable)
        LaserBeam.containers = (self.updatable, self.drawable, self.laser_beams)

        self.table: Table = Table(screen)
        # The currently selected mirror
        self.selected_mirror: Mirror | None = None
        self.selected_laser: Laser | None = None
        # Whether dragging is active
        self.dragging: bool = False
        # The open degree-entry box, if any
        self.input_box: InputBox | None = None
        # Where the left button went down, and which existing object it landed on, so
        # that a click can be told apart from a drag once the button comes back up
        self.press_pos: tuple[int, int] | None = None
        self.click_target: Orientable | None = None
        # Kept from update() so the post-draw sprite pass can use it, see draw()
        self._dt: float = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.table.resize(event)
            return

        # An open degree box swallows every other interaction, so the click
        # that dismisses it cannot also grab the object underneath
        if self.input_box is not None:
            if self.input_box.handle_event(event):
                self.input_box = None
            return

        # Escape backs out to the menu, but only once the degree box above has
        # had its chance to treat Escape as "cancel my edit"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from menu import MenuScene  # local import: menu.py imports this module
            self.go_to(MenuScene(self.screen))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.press_pos = event.pos
            self.click_target = None
            mirror_rect_in_table = self.table.entry_rects.get("mirror")
            laser_rect_in_table = self.table.entry_rects.get("laser")
            # Check if the click is on the mirror in the table
            if mirror_rect_in_table and mirror_rect_in_table.collidepoint(event.pos):
                # Create a new mirror object at the mouse position
                mouse_x, mouse_y = event.pos
                new_mirror = Mirror(mouse_x, mouse_y, self.screen)
                self.selected_mirror = new_mirror
                self.dragging = True
            else:
                # Check if any mirror is clicked in the main area
                for mirror in self.mirrors:
                    if mirror.rect is not None and mirror.rect.collidepoint(event.pos):
                        self.selected_mirror = mirror
                        self.click_target = mirror
                        self.dragging = True
                        break
            # Check if the click is on the laser in the table
            if laser_rect_in_table and laser_rect_in_table.collidepoint(event.pos):
                # Create a new laser object at the mouse position
                mouse_x, mouse_y = event.pos
                new_laser = Laser(mouse_x, mouse_y, self.screen)
                self.selected_laser = new_laser
                self.dragging = True
            else:
                # Check if any laser is clicked in the main area
                for laser in self.lasers:
                    if laser.rect is not None and laser.rect.collidepoint(event.pos):
                        self.selected_laser = laser
                        self.click_target = laser
                        self.dragging = True
                        break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # A press and release that barely moved is a click, not a drag, and
            # opens the degree box on the object it landed on. Objects just
            # created from the table are excluded, they are being dragged out.
            if self.click_target is not None and self.press_pos is not None:
                moved_x = abs(event.pos[0] - self.press_pos[0])
                moved_y = abs(event.pos[1] - self.press_pos[1])
                if moved_x <= CLICK_MOVE_THRESHOLD and moved_y <= CLICK_MOVE_THRESHOLD:
                    self.input_box = InputBox(self.click_target, self.screen, self.table.width)
            self.dragging = False
            self.selected_mirror = None
            self.selected_laser = None
            self.press_pos = None
            self.click_target = None
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for laser in self.lasers:
                if laser.rect is not None and laser.rect.collidepoint(event.pos):
                    if not laser.laser_on:
                        laser.laser_on = True
                        laser_start = laser.get_laser_point()
                        laser.laser_beam = LaserBeam(laser_start, self.screen, laser.orientation, self.mirrors)
                    else:
                        laser.laser_on = False
                        assert laser.laser_beam is not None
                        laser.laser_beam.kill()
                        laser.laser_beam = None

    def update(self, dt: float) -> None:
        # The sprite update pass lives in draw() instead of here on purpose:
        # every Mirror/Laser recomputes its rect inside its own draw(), and
        # update()/check_delete() read that rect, so they have to run after it.
        self._dt = dt

        # Update the position of the selected mirror during dragging
        if self.input_box is None:
            if self.dragging and self.selected_mirror:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.selected_mirror.set_position(mouse_x, mouse_y)
            elif self.dragging and self.selected_laser:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.selected_laser.set_position(mouse_x, mouse_y)
                if self.selected_laser.laser_beam:
                    self.selected_laser.laser_beam.start_pos = self.selected_laser.get_laser_point()

    def draw(self) -> None:
        # Fill the screen with a color to wipe away anything from the last frame
        self.screen.fill("black")

        # Draw the table and other elements
        self.table.draw()
        for obj in self.drawable:
            obj.draw()

        if self.input_box is None:
            for obj in self.updatable:
                obj.update(self._dt)

            for obj in self.deletable:
                obj.check_delete(self.table.rect)
        else:
            # Beams keep tracking their mirrors, but the A/D rotation keys are
            # suspended so typing into the box cannot also spin the object
            for beam in self.laser_beams:
                beam.update(self._dt)
            self.input_box.draw()
