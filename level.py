import pygame

from constants import *
from input_box import InputBox
from laser import Laser
from laserbeam import LaserBeam
from levels import LevelLayout, next_level
from mirror import Mirror
from overlay import ChoiceOverlay, OverlayChoice
from render_utils import render_text
from scene import Scene
from target import Target


class LevelScene(Scene):
    # A single laser-chess puzzle: a fixed laser, a target, and mirrors the
    # player rotates until the beam lands on the target. Rotate by hovering a
    # mirror and holding A/D, or click one to type an exact angle.
    def __init__(self, screen: pygame.Surface, layout: LevelLayout) -> None:
        super().__init__(screen)
        self.layout: LevelLayout = layout

        # Board geometry, centered on the screen
        self.board_width: int = BOARD_COLS * BOARD_CELL_SIZE
        self.board_height: int = BOARD_ROWS * BOARD_CELL_SIZE
        self.board_left: int = (screen.get_width() - self.board_width) // 2
        self.board_top: int = (screen.get_height() - self.board_height) // 2

        # Pieces are built with add_to_groups=False so a level never lands in
        # whatever sprite groups the sandbox last configured
        laser_x, laser_y = self.cell_center(*layout.laser_cell)
        self.laser: Laser = Laser(
            laser_x, laser_y, screen,
            length=LEVEL_LASER_LENGTH,
            orientation=layout.laser_orientation,
            add_to_groups=False,
        )
        self.mirrors: pygame.sprite.Group = pygame.sprite.Group()
        for spec in layout.mirrors:
            mirror_x, mirror_y = self.cell_center(*spec.cell)
            self.mirrors.add(
                Mirror(
                    mirror_x, mirror_y, screen,
                    length=LEVEL_MIRROR_LENGTH,
                    orientation=spec.orientation,
                    add_to_groups=False,
                )
            )
        target_x, target_y = self.cell_center(*layout.target_cell)
        self.target: Target = Target(target_x, target_y, screen)

        # Created on the first frame, once the pieces have been drawn once and
        # so have the geometry the beam traces against
        self.beam: LaserBeam | None = None
        self.laser.laser_on = True

        self.hint_font: pygame.font.Font = pygame.font.SysFont("Arial", LEVEL_HINT_FONT_SIZE)
        self.input_box: InputBox | None = None
        self.won: bool = False
        self.win_overlay: ChoiceOverlay | None = None

    def cell_center(self, col: int, row: int) -> tuple[float, float]:
        return (
            self.board_left + col * BOARD_CELL_SIZE + BOARD_CELL_SIZE / 2,
            self.board_top + row * BOARD_CELL_SIZE + BOARD_CELL_SIZE / 2,
        )

    # -- navigation, wired into the win overlay ---------------------------

    def go_to_level_select(self) -> None:
        from level_select import LevelSelectScene  # local import: it builds LevelScenes

        self.go_to(LevelSelectScene(self.screen))

    def go_to_next_level(self) -> None:
        # Does nothing while this is the last level. Add another entry to
        # LEVELS and this button starts working with no change here.
        following = next_level(self.layout)
        if following is not None:
            self.go_to(LevelScene(self.screen, following))

    def _build_win_overlay(self) -> ChoiceOverlay:
        return ChoiceOverlay(
            self.screen,
            LEVEL_WIN_TITLE,
            [
                OverlayChoice("Level Select", self.go_to_level_select),
                OverlayChoice(
                    "Next Level",
                    self.go_to_next_level,
                    enabled=next_level(self.layout) is not None,
                ),
            ],
        )

    # -- scene interface ---------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        # A finished level is modal: the overlay takes everything
        if self.win_overlay is not None:
            self.win_overlay.handle_event(event)
            return

        # An open degree box swallows every other interaction, including its
        # own Escape-to-cancel, before Escape can mean "leave the level"
        if self.input_box is not None:
            if self.input_box.handle_event(event):
                self.input_box = None
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_to_level_select()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for mirror in self.mirrors:
                if mirror.rect is not None and mirror.rect.collidepoint(event.pos):
                    self.input_box = InputBox(mirror, self.screen, self.screen.get_width())
                    return

    def update(self, dt: float) -> None:
        if self.won or self.input_box is not None:
            return
        # Guarded rather than asserted: a mirror has no rect until its first
        # draw(), and update() reads that rect to see if it is hovered
        for mirror in self.mirrors:
            if mirror.rect is not None:
                mirror.update(dt)

    def draw(self) -> None:
        self.screen.fill("black")
        self._draw_board()

        # Drawing a piece is also what recomputes its geometry, so everything
        # the beam traces against has to be drawn before the beam is traced
        self.target.draw(hit=self.won)
        self.laser.draw()
        for mirror in self.mirrors:
            mirror.draw()

        if self.beam is None:
            self.beam = LaserBeam(
                self.laser.get_laser_point(),
                self.screen,
                self.laser.orientation,
                self.mirrors,
                add_to_groups=False,
                right_boundary=self.screen.get_width(),
            )
        else:
            self.beam.compute_beam_path()
        self.beam.draw()

        self._draw_hint()

        if not self.won and self.target.is_hit_by(self.beam.beam_path):
            self.won = True
            self.win_overlay = self._build_win_overlay()

        if self.input_box is not None:
            self.input_box.draw()
        if self.win_overlay is not None:
            self.win_overlay.draw()

    # -- drawing helpers ---------------------------------------------------

    def _draw_board(self) -> None:
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                cell = pygame.Rect(
                    self.board_left + col * BOARD_CELL_SIZE,
                    self.board_top + row * BOARD_CELL_SIZE,
                    BOARD_CELL_SIZE,
                    BOARD_CELL_SIZE,
                )
                shade = BOARD_LIGHT_CELL if (col + row) % 2 == 0 else BOARD_DARK_CELL
                pygame.draw.rect(self.screen, shade, cell)
                pygame.draw.rect(self.screen, BOARD_GRID_COLOR, cell, 1)

    def _draw_hint(self) -> None:
        hint_text, hint_rect = render_text(
            self.hint_font,
            self.layout.hint,
            LEVEL_HINT_COLOR,
            (self.screen.get_width() // 2, self.board_top + self.board_height + LEVEL_HINT_FONT_SIZE * 2),
        )
        self.screen.blit(hint_text, hint_rect)
