import pygame

from constants import *
from input_box import InputBox
from laser import Laser
from laserbeam import LaserBeam
from levels import LevelLayout, next_level
from mirror import Mirror
from overlay import ChoiceOverlay, OverlayChoice
from render_utils import render_text
from scene import Scene, SceneFactory
from target import Target


def _default_exit(screen: pygame.Surface) -> Scene:
    from level_select import LevelSelectScene  # local import: it builds LevelScenes

    return LevelSelectScene(screen)


class LevelScene(Scene):
    # A single laser-chess puzzle: a fixed laser, a target, and mirrors the
    # player rotates until the beam lands on the target. Rotate by hovering a
    # mirror and holding A/D, or click one to type an exact angle.
    def __init__(
        self,
        screen: pygame.Surface,
        layout: LevelLayout,
        playlist: list[LevelLayout] | None = None,
        on_exit: SceneFactory | None = None,
    ) -> None:
        super().__init__(screen)
        self.layout: LevelLayout = layout
        # Which set this level belongs to, and where leaving it goes. Custom
        # levels pass their own pair so that "Next Level" walks the player's
        # own levels and Escape goes back to the list they came from. Left as
        # None the built-in set is used, looked up when it is needed rather
        # than captured here.
        self.playlist: list[LevelLayout] | None = playlist
        self.on_exit: SceneFactory = _default_exit if on_exit is None else on_exit

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

        # What each mirror started at, so the level can tell whether the
        # player has actually moved anything yet
        self._start_orientations: dict[Mirror, float] = {
            mirror: mirror.orientation
            for mirror in self.mirrors
            if isinstance(mirror, Mirror)
        }
        # A level with nothing to rotate has no move to wait for, so it is
        # treated as touched from the start rather than as unwinnable
        self.touched: bool = not self._start_orientations

        self.hint_font: pygame.font.Font = pygame.font.SysFont("Arial", LEVEL_HINT_FONT_SIZE)
        # What the line under the board currently says, refreshed each frame
        self.footer_text: str = layout.hint
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
        self.go_to(self.on_exit(self.screen))

    def go_to_next_level(self) -> None:
        # Does nothing while this is the last level. Add another entry to
        # LEVELS and this button starts working with no change here.
        following = next_level(self.layout, self.playlist)
        if following is not None:
            self.go_to(LevelScene(self.screen, following, self.playlist, self.on_exit))

    def _build_win_overlay(self) -> ChoiceOverlay:
        return ChoiceOverlay(
            self.screen,
            LEVEL_WIN_TITLE,
            [
                OverlayChoice("Level Select", self.go_to_level_select),
                OverlayChoice(
                    "Next Level",
                    self.go_to_next_level,
                    enabled=next_level(self.layout, self.playlist) is not None,
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

        self._note_interaction()
        on_target = self.target.is_hit_by(self.beam.beam_path)
        if not self.won and self.touched and on_target:
            self.won = True
            self.win_overlay = self._build_win_overlay()

        self.footer_text = (
            LEVEL_UNTOUCHED_HINT if on_target and not self.touched else self.layout.hint
        )
        self._draw_hint()

        if self.input_box is not None:
            self.input_box.draw()
        if self.win_overlay is not None:
            self.win_overlay.draw()

    def _note_interaction(self) -> None:
        # A level is only solved once the player has moved a mirror, so one
        # that happens to start with the beam already on the target -- easy to
        # build in the editor -- cannot be won before it has been played. The
        # flag sticks: turning a mirror back to where it started still counts.
        if self.touched:
            return
        self.touched = any(
            mirror.orientation != start
            for mirror, start in self._start_orientations.items()
        )

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
            self.footer_text,
            LEVEL_HINT_COLOR,
            (self.screen.get_width() // 2, self.board_top + self.board_height + LEVEL_HINT_FONT_SIZE * 2),
        )
        self.screen.blit(hint_text, hint_rect)
