from itertools import chain
from typing import Callable

import pygame

from constants import *
from input_box import InputBox, Orientable
from laser import Laser
from laserbeam import LaserBeam
from mirror import Mirror
from scene import Scene
from table import SANDBOX_ENTRIES, Table
from wall import Wall

# Anything free play can put on the screen and drag around
SandboxPiece = Mirror | Laser | Wall
# Makes a new one at the point it was dragged out to. These join the sprite
# groups, unlike the samples the table draws (see table.py).
PieceFactory = Callable[[float, float, pygame.Surface], SandboxPiece]


def _new_mirror(x: float, y: float, screen: pygame.Surface) -> SandboxPiece:
    return Mirror(x, y, screen, length=MIRROR_LENGTH)


def _new_laser(x: float, y: float, screen: pygame.Surface) -> SandboxPiece:
    return Laser(x, y, screen, length=LASER_LENGTH)


def _new_wall(x: float, y: float, screen: pygame.Surface) -> SandboxPiece:
    return Wall(x, y, screen, length=WALL_LENGTH)


# Keyed by the name the table lists the piece under, so dragging one out
# produces the object its sample was drawn from
NEW_PIECES: dict[str, PieceFactory] = {
    "mirror": _new_mirror,
    "laser": _new_laser,
    "wall": _new_wall,
}


class SandboxScene(Scene):
    # Free-play mode: drag mirrors, lasers and walls off the table, aim them,
    # and switch beams on. This is the behaviour the app used to boot straight
    # into.
    def __init__(self, screen: pygame.Surface) -> None:
        super().__init__(screen)

        # Make groups for all the relevant collections of objects
        self.updatable: pygame.sprite.Group = pygame.sprite.Group()
        self.drawable: pygame.sprite.Group = pygame.sprite.Group()
        self.deletable: pygame.sprite.Group = pygame.sprite.Group()  # Objects that can be dragged to the table and deleted
        self.mirrors: pygame.sprite.Group = pygame.sprite.Group()
        self.lasers: pygame.sprite.Group = pygame.sprite.Group()
        self.walls: pygame.sprite.Group = pygame.sprite.Group()
        self.laser_beams: pygame.sprite.Group = pygame.sprite.Group()
        Mirror.containers = (self.updatable, self.drawable, self.mirrors, self.deletable)
        Laser.containers = (self.updatable, self.drawable, self.lasers, self.deletable)
        Wall.containers = (self.updatable, self.drawable, self.walls, self.deletable)
        LaserBeam.containers = (self.updatable, self.drawable, self.laser_beams)

        self.table: Table = Table(screen, SANDBOX_ENTRIES)
        # The piece being dragged, whichever kind it is
        self.selected: SandboxPiece | None = None
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

    def pieces(self) -> list[SandboxPiece]:
        # Everything on the screen that can be picked up, newest last
        return list(chain(self.mirrors, self.lasers, self.walls))

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
            self._on_press(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_release(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self._toggle_laser(event.pos)

    def _on_press(self, pos: tuple[int, int]) -> None:
        self.press_pos = pos
        self.click_target = None

        # A press on one of the table's entries drags a new piece of that kind out
        for name, make_piece in NEW_PIECES.items():
            entry_rect = self.table.entry_rects.get(name)
            if entry_rect is not None and entry_rect.collidepoint(pos):
                self.selected = make_piece(pos[0], pos[1], self.screen)
                self.dragging = True
                return

        # Otherwise it picks up a piece already on the screen
        for piece in self.pieces():
            if piece.rect is not None and piece.rect.collidepoint(pos):
                self.selected = piece
                self.click_target = piece
                self.dragging = True
                return

    def _on_release(self, pos: tuple[int, int]) -> None:
        # A press and release that barely moved is a click, not a drag, and
        # opens the degree box on the object it landed on. Objects just
        # created from the table are excluded, they are being dragged out.
        if self.click_target is not None and self.press_pos is not None:
            moved_x = abs(pos[0] - self.press_pos[0])
            moved_y = abs(pos[1] - self.press_pos[1])
            if moved_x <= CLICK_MOVE_THRESHOLD and moved_y <= CLICK_MOVE_THRESHOLD:
                self.input_box = InputBox(self.click_target, self.screen, self.table.width)
        self.dragging = False
        self.selected = None
        self.press_pos = None
        self.click_target = None

    def _toggle_laser(self, pos: tuple[int, int]) -> None:
        for laser in self.lasers:
            if laser.rect is not None and laser.rect.collidepoint(pos):
                if not laser.laser_on:
                    laser.laser_on = True
                    laser.laser_beam = LaserBeam(
                        laser.get_laser_point(),
                        self.screen,
                        laser.orientation,
                        self.mirrors,
                        walls=self.walls,
                    )
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

        # Update the position of the selected object during dragging
        if self.input_box is None and self.dragging and self.selected is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.selected.set_position(mouse_x, mouse_y)
            if isinstance(self.selected, Laser) and self.selected.laser_beam:
                self.selected.laser_beam.start_pos = self.selected.get_laser_point()

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
