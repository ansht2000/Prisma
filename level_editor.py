"""Build your own level: drag pieces off the table onto a level board and
save the result to custom_levels/ as a TOML file (see custom_levels.py).

Laid out like the sandbox -- pieces on the right, working area on the left --
except that the working area is a level's checkerboard, and a piece dropped on
it snaps to the middle of the square it landed on. Dropping a piece anywhere
off the board throws it away, the way the sandbox deletes a piece dragged back
to the table.
"""
from pathlib import Path
from typing import Literal

import pygame

from button import Button
from constants import *
from custom_levels import CUSTOM_LEVELS_DIR, CustomLevel, save
from input_box import InputBox
from laser import Laser
from levels import Cell, MirrorSpec
from mirror import Mirror
from render_utils import render_text
from save_dialog import SaveDialog
from scene import Scene
from table import EDITOR_ENTRIES, Table
from target import Target

PieceKind = Literal["mirror", "laser", "target"]
PieceObject = Mirror | Laser | Target

# The pieces the table offers, in the order it lists them
PIECE_KINDS: tuple[PieceKind, ...] = ("mirror", "laser", "target")

EDITOR_HINT: str = "Drag pieces onto the board. Click a placed piece to set its angle."


class Piece:
    # One mirror, laser or target on the editor board. Wraps the real game
    # object so the editor draws exactly what a level will, and satisfies
    # input_box.Orientable, so clicking one can open the degree box.
    def __init__(self, kind: PieceKind, screen: pygame.Surface) -> None:
        self.kind: PieceKind = kind
        self.screen: pygame.Surface = screen
        # None until the piece is dropped on a square; a piece being dragged
        # around has a position but does not belong to a cell yet
        self.cell: Cell | None = None
        self.rect: pygame.Rect | None = None
        self.object: PieceObject = self._build(kind, screen)

    @staticmethod
    def _build(kind: PieceKind, screen: pygame.Surface) -> PieceObject:
        # Built at the origin and moved into place by set_position(), and out
        # of the sprite groups so an editor piece never joins a running game
        if kind == "mirror":
            return Mirror(0, 0, screen, length=LEVEL_MIRROR_LENGTH, add_to_groups=False)
        if kind == "laser":
            return Laser(0, 0, screen, length=LEVEL_LASER_LENGTH, add_to_groups=False)
        return Target(0, 0, screen)

    @property
    def orientation(self) -> float:
        if isinstance(self.object, Target):
            return 0.0  # a target has no facing: it is hit from any direction
        return self.object.orientation

    def set_position(self, x: float, y: float) -> None:
        self.object.set_position(x, y)

    def set_orientation(self, degrees: float) -> None:
        if isinstance(self.object, Target):
            return
        self.object.set_orientation(degrees)

    def draw(self) -> None:
        self.object.draw()
        self.rect = self.object.rect


class LevelEditorScene(Scene):
    def __init__(self, screen: pygame.Surface, directory: Path | None = None) -> None:
        super().__init__(screen)
        # Injectable so a test can save somewhere other than the real
        # custom_levels/ directory
        self.directory: Path = CUSTOM_LEVELS_DIR if directory is None else directory
        self.table: Table = Table(screen, EDITOR_ENTRIES)

        self.pieces: list[Piece] = []
        # The piece currently following the mouse, if any. It is deliberately
        # kept out of self.pieces: it is not on the board until it is dropped.
        self.held: Piece | None = None
        # Where the left button went down, and the placed piece it landed on,
        # so a click can be told apart from a drag once the button comes up
        self.press_pos: tuple[int, int] | None = None
        self.click_target: Piece | None = None

        self.input_box: InputBox | None = None
        self.dialog: SaveDialog | None = None
        self.status: str = ""
        self.status_timer: float = 0

        self.hint_font: pygame.font.Font = pygame.font.SysFont("Arial", LEVEL_HINT_FONT_SIZE)
        self.status_font: pygame.font.Font = pygame.font.SysFont("Arial", EDITOR_STATUS_FONT_SIZE)
        self.button_font: pygame.font.Font = pygame.font.SysFont("Arial", EDITOR_SAVE_FONT_SIZE)
        self.board_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.save_button: Button = Button(
            EDITOR_SAVE_LABEL, pygame.Rect(0, 0, 0, 0), self.button_font
        )
        self._layout()

    def _layout(self) -> None:
        # The board sits in the area the table leaves free, with the save
        # button and one line of text stacked underneath it
        board_width = BOARD_COLS * BOARD_CELL_SIZE
        board_height = BOARD_ROWS * BOARD_CELL_SIZE
        footer = EDITOR_BOARD_GAP + EDITOR_SAVE_BUTTON_HEIGHT + EDITOR_BOARD_GAP + LEVEL_HINT_FONT_SIZE
        top = max((self.screen.get_height() - board_height - footer) // 2, EDITOR_BOARD_TOP_MIN)
        left = max((int(self.table.width) - board_width) // 2, 0)

        self.board_rect = pygame.Rect(left, top, board_width, board_height)
        self.save_button.rect = pygame.Rect(
            self.board_rect.centerx - EDITOR_SAVE_BUTTON_WIDTH // 2,
            self.board_rect.bottom + EDITOR_BOARD_GAP,
            EDITOR_SAVE_BUTTON_WIDTH,
            EDITOR_SAVE_BUTTON_HEIGHT,
        )

    # -- board geometry ----------------------------------------------------

    def cell_center(self, col: int, row: int) -> tuple[float, float]:
        return (
            self.board_rect.left + col * BOARD_CELL_SIZE + BOARD_CELL_SIZE / 2,
            self.board_rect.top + row * BOARD_CELL_SIZE + BOARD_CELL_SIZE / 2,
        )

    def cell_at(self, pos: tuple[float, float]) -> Cell:
        # The square a point falls in -- which, for a point on the board, is
        # also the square whose center it is nearest. Points off the board
        # clamp to the edge square rather than running off the grid.
        col = int((pos[0] - self.board_rect.left) // BOARD_CELL_SIZE)
        row = int((pos[1] - self.board_rect.top) // BOARD_CELL_SIZE)
        return (
            max(0, min(col, BOARD_COLS - 1)),
            max(0, min(row, BOARD_ROWS - 1)),
        )

    def piece_at(self, cell: Cell) -> Piece | None:
        for piece in self.pieces:
            if piece.cell == cell:
                return piece
        return None

    def piece_of_kind(self, kind: PieceKind) -> Piece | None:
        for piece in self.pieces:
            if piece.kind == kind:
                return piece
        return None

    # -- editing -----------------------------------------------------------

    def place(self, piece: Piece, cell: Cell) -> None:
        # A square holds one piece, and a level has one laser and one target,
        # so either of those replaces whatever it displaces
        occupant = self.piece_at(cell)
        if occupant is not None:
            self.pieces.remove(occupant)
        if piece.kind in ("laser", "target"):
            existing = self.piece_of_kind(piece.kind)
            if existing is not None:
                self.pieces.remove(existing)
        piece.cell = cell
        self.pieces.append(piece)

    def to_level(self, name: str) -> CustomLevel:
        laser = self.piece_of_kind("laser")
        target = self.piece_of_kind("target")
        return CustomLevel(
            name=name,
            laser_cell=None if laser is None else _cell_of(laser),
            laser_orientation=0.0 if laser is None else laser.orientation,
            target_cell=None if target is None else _cell_of(target),
            mirrors=tuple(
                MirrorSpec(cell=_cell_of(piece), orientation=piece.orientation)
                for piece in self.pieces
                if piece.kind == "mirror"
            ),
        )

    def save_level(self, name: str) -> Path | None:
        # Returns where the level landed, or None if it could not be written
        try:
            path = save(self.to_level(name), self.directory)
        except OSError as error:
            self._show_status(f"Could not save: {error.strerror or error}")
            return None
        self._show_status(f"Saved {path.name}")
        return path

    def _adopt_screen(self, screen: pygame.Surface) -> None:
        # Resizing the window hands back a brand new surface, and everything
        # here draws onto the one it was built with -- so pass the new one on,
        # or the board would be the only thing left visible
        self.screen = screen
        for piece in self.pieces:
            piece.object.screen = screen
        if self.held is not None:
            self.held.object.screen = screen
        if self.input_box is not None:
            self.input_box.screen = screen
        if self.dialog is not None:
            self.dialog.screen = screen

    def _show_status(self, message: str) -> None:
        self.status = message
        self.status_timer = EDITOR_STATUS_SECONDS

    # -- scene interface ---------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.table.resize(event)
            self._adopt_screen(self.table.screen)
            self._layout()
            return

        # The save prompt is modal, and takes Escape as "cancel my save"
        # before Escape can mean "leave the editor"
        if self.dialog is not None:
            result = self.dialog.handle_event(event)
            if result is not None:
                self.dialog = None
                if result.confirmed:
                    self.save_level(result.name)
            return

        # An open degree box swallows everything else, so the click that
        # dismisses it cannot also grab the piece underneath
        if self.input_box is not None:
            if self.input_box.handle_event(event):
                self.input_box = None
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from menu import MenuScene  # local import: menu.py imports this module

            self.go_to(MenuScene(self.screen))
            return

        if event.type == pygame.MOUSEMOTION:
            self.save_button.hovered = self.save_button.contains(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_press(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._on_release(event.pos)

    def _on_press(self, pos: tuple[int, int]) -> None:
        self.press_pos = pos
        self.click_target = None

        if self.save_button.contains(pos):
            self.dialog = SaveDialog(self.screen)
            return

        # A press on the table starts a brand new piece of that kind
        for kind in PIECE_KINDS:
            entry_rect = self.table.entry_rects.get(kind)
            if entry_rect is not None and entry_rect.collidepoint(pos):
                held = Piece(kind, self.screen)
                held.set_position(*pos)
                self.held = held
                return

        # Otherwise it picks up a piece already on the board. Later pieces are
        # drawn on top, so the search runs back to front.
        for piece in reversed(self.pieces):
            if piece.rect is not None and piece.rect.collidepoint(pos):
                self.pieces.remove(piece)
                self.held = piece
                self.click_target = piece
                return

    def _on_release(self, pos: tuple[int, int]) -> None:
        held = self.held
        self.held = None
        press_pos = self.press_pos
        self.press_pos = None
        click_target = self.click_target
        self.click_target = None

        if held is None:
            return

        # A press and release that barely moved is a click, not a drag: the
        # piece goes back where it was and opens its degree box. Pieces just
        # taken off the table are excluded, they are being dragged out.
        if held is click_target and press_pos is not None and _is_click(press_pos, pos):
            assert held.cell is not None  # it was on the board a moment ago
            self.place(held, held.cell)
            if held.rect is not None and held.kind != "target":
                self.input_box = InputBox(held, self.screen, self.table.width)
            return

        if self.board_rect.collidepoint(pos):
            self.place(held, self.cell_at(pos))
        # Dropped anywhere else -- the table, the margins -- the piece is
        # simply not kept, which is how a piece gets deleted

    def update(self, dt: float) -> None:
        if self.status_timer > 0:
            self.status_timer = max(self.status_timer - dt, 0)
            if self.status_timer == 0:
                self.status = ""

        if self.dialog is not None or self.input_box is not None:
            return

        if self.held is not None:
            mouse_pos = pygame.mouse.get_pos()
            if self.board_rect.collidepoint(mouse_pos):
                # Snap while dragging, so where the piece will land is obvious
                # before the button comes up
                self.held.set_position(*self.cell_center(*self.cell_at(mouse_pos)))
            else:
                self.held.set_position(*mouse_pos)

    def draw(self) -> None:
        self.screen.fill("black")
        self._draw_board()

        for piece in self.pieces:
            assert piece.cell is not None  # place() gives every placed piece one
            piece.set_position(*self.cell_center(*piece.cell))
            piece.draw()

        self.table.draw()
        self.save_button.draw(self.screen)
        self._draw_footer()

        # Last, so the piece being dragged stays on top of the board and the table
        if self.held is not None:
            self.held.draw()

        if self.input_box is not None:
            self.input_box.draw()
        if self.dialog is not None:
            self.dialog.draw()

    # -- drawing helpers ---------------------------------------------------

    def _draw_board(self) -> None:
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                cell = pygame.Rect(
                    self.board_rect.left + col * BOARD_CELL_SIZE,
                    self.board_rect.top + row * BOARD_CELL_SIZE,
                    BOARD_CELL_SIZE,
                    BOARD_CELL_SIZE,
                )
                shade = BOARD_LIGHT_CELL if (col + row) % 2 == 0 else BOARD_DARK_CELL
                pygame.draw.rect(self.screen, shade, cell)
                pygame.draw.rect(self.screen, BOARD_GRID_COLOR, cell, 1)

    def _draw_footer(self) -> None:
        # One line under the save button: whatever just happened, or, once
        # that has faded, how to work the editor
        font = self.status_font if self.status else self.hint_font
        color = EDITOR_STATUS_COLOR if self.status else LEVEL_HINT_COLOR
        text, rect = render_text(
            font,
            self.status or EDITOR_HINT,
            color,
            (self.board_rect.centerx, self.save_button.rect.bottom + EDITOR_BOARD_GAP),
        )
        self.screen.blit(text, rect)


def _cell_of(piece: Piece) -> Cell:
    assert piece.cell is not None  # place() gives every placed piece one
    return piece.cell


def _is_click(press_pos: tuple[int, int], release_pos: tuple[int, int]) -> bool:
    return (
        abs(release_pos[0] - press_pos[0]) <= CLICK_MOVE_THRESHOLD
        and abs(release_pos[1] - press_pos[1]) <= CLICK_MOVE_THRESHOLD
    )
