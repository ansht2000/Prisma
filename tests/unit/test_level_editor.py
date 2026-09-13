"""Unit tests for LevelEditorScene: dragging pieces off the table onto the
board, snapping them to squares, and saving the result.

The table only knows where its entries are once it has drawn itself, so every
test that drags a piece off it draws the scene first, exactly as the app loop
does before the first click can arrive.
"""
import tomllib
from pathlib import Path

import pygame
import pytest

from constants import (
    BOARD_CELL_SIZE,
    BOARD_COLS,
    BOARD_ROWS,
    CLICK_MOVE_THRESHOLD,
    EDITOR_NO_LEVELS_MESSAGE,
    EDITOR_SAVE_BUTTON_WIDTH,
)
from custom_levels import CustomLevel, save, save_to
from input_box import InputBox
from level_editor import EDITOR_HINT, LevelEditorScene, Piece, PieceKind
from levels import MirrorSpec, WallSpec
from menu import MenuScene
from save_dialog import SaveDialog

pytestmark = pytest.mark.unit


@pytest.fixture
def editor(screen: pygame.Surface, tmp_path: Path) -> LevelEditorScene:
    """An editor that saves into a throwaway directory, already drawn once."""
    scene = LevelEditorScene(screen, tmp_path)
    scene.draw()
    return scene


def press(scene: LevelEditorScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}))


def release(scene: LevelEditorScene, pos: tuple[float, float]) -> None:
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1}))


def key(scene: LevelEditorScene, code: int, unicode: str = "") -> None:
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": code, "unicode": unicode}))


def type_text(scene: LevelEditorScene, text: str) -> None:
    for char in text:
        key(scene, ord(char), char)


def table_pos(scene: LevelEditorScene, kind: str) -> tuple[float, float]:
    rect = scene.table.entry_rects[kind]
    return rect.center


def drag_from_table(scene: LevelEditorScene, kind: str, to: tuple[float, float]) -> None:
    press(scene, table_pos(scene, kind))
    release(scene, to)


def cell_pos(scene: LevelEditorScene, col: int, row: int) -> tuple[float, float]:
    return scene.cell_center(col, row)


class TestLayout:
    def test_the_board_has_a_square_for_every_cell(self, editor: LevelEditorScene) -> None:
        assert editor.board_rect.width == BOARD_COLS * BOARD_CELL_SIZE
        assert editor.board_rect.height == BOARD_ROWS * BOARD_CELL_SIZE

    def test_the_board_stays_clear_of_the_table(self, editor: LevelEditorScene) -> None:
        assert editor.board_rect.right <= editor.table.width

    def test_the_save_and_load_buttons_sit_under_the_board(
        self, editor: LevelEditorScene
    ) -> None:
        assert editor.save_button.rect.top >= editor.board_rect.bottom
        assert editor.load_button.rect.top == editor.save_button.rect.top

    def test_load_sits_next_to_save(self, editor: LevelEditorScene) -> None:
        gap = editor.load_button.rect.left - editor.save_button.rect.right

        assert 0 < gap < EDITOR_SAVE_BUTTON_WIDTH
        # and the pair as a whole is centered under the board
        middle = (editor.save_button.rect.left + editor.load_button.rect.right) // 2
        assert abs(middle - editor.board_rect.centerx) <= 1

    def test_everything_stays_on_screen(self, editor: LevelEditorScene, screen: pygame.Surface) -> None:
        assert editor.board_rect.top >= 0
        assert editor.save_button.rect.bottom <= screen.get_height()
        assert editor.load_button.rect.right <= editor.table.width

    def test_the_table_offers_a_target_as_well(self, editor: LevelEditorScene) -> None:
        assert set(editor.table.entry_rects) >= {"mirror", "laser", "target"}


class TestDraggingFromTheTable:
    @pytest.mark.parametrize("kind", ["mirror", "laser", "target"])
    def test_a_piece_dropped_on_the_board_is_kept(self, editor: LevelEditorScene, kind: str) -> None:
        drag_from_table(editor, kind, cell_pos(editor, 3, 2))

        assert [p.kind for p in editor.pieces] == [kind]

    def test_a_piece_dropped_off_the_board_is_thrown_away(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", table_pos(editor, "mirror"))

        assert editor.pieces == []

    def test_pressing_the_table_does_not_place_anything_on_its_own(
        self, editor: LevelEditorScene
    ) -> None:
        press(editor, table_pos(editor, "mirror"))

        assert editor.pieces == []
        assert editor.held is not None

    def test_several_mirrors_can_be_placed(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 0, 0))
        drag_from_table(editor, "mirror", cell_pos(editor, 1, 1))
        drag_from_table(editor, "mirror", cell_pos(editor, 2, 2))

        assert len(editor.pieces) == 3


class TestSnapping:
    def test_a_drop_anywhere_in_a_square_lands_on_its_cell(self, editor: LevelEditorScene) -> None:
        corner = (
            editor.board_rect.left + 3 * BOARD_CELL_SIZE + 2,
            editor.board_rect.top + 2 * BOARD_CELL_SIZE + 2,
        )

        drag_from_table(editor, "mirror", corner)

        assert editor.pieces[0].cell == (3, 2)

    def test_a_placed_piece_is_drawn_at_the_center_of_its_square(
        self, editor: LevelEditorScene
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()

        placed = editor.pieces[0]
        assert placed.rect is not None
        assert placed.rect.center == pytest.approx(cell_pos(editor, 3, 2), abs=1)

    def test_the_cell_under_a_point_is_the_one_containing_it(
        self, editor: LevelEditorScene
    ) -> None:
        assert editor.cell_at(cell_pos(editor, 5, 4)) == (5, 4)
        assert editor.cell_at((editor.board_rect.left + 1, editor.board_rect.top + 1)) == (0, 0)

    def test_points_off_the_board_clamp_to_the_edge_squares(
        self, editor: LevelEditorScene
    ) -> None:
        assert editor.cell_at((-500, -500)) == (0, 0)
        assert editor.cell_at((10_000, 10_000)) == (BOARD_COLS - 1, BOARD_ROWS - 1)

    def test_a_held_piece_snaps_while_it_is_over_the_board(
        self, editor: LevelEditorScene, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        held = Piece("mirror", editor.screen)
        editor.held = held
        center = cell_pos(editor, 4, 1)
        # The dummy video driver pins the real cursor at the origin, so the
        # pointer position is supplied rather than moved
        monkeypatch.setattr(
            pygame.mouse, "get_pos", lambda: (int(center[0]) + 10, int(center[1]) + 10)
        )

        editor.update(0.016)

        assert (held.object.pos_x, held.object.pos_y) == pytest.approx(center)

    def test_a_held_piece_follows_the_pointer_off_the_board(
        self, editor: LevelEditorScene, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        held = Piece("mirror", editor.screen)
        editor.held = held
        outside = table_pos(editor, "mirror")
        monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (int(outside[0]), int(outside[1])))

        editor.update(0.016)

        assert (held.object.pos_x, held.object.pos_y) == pytest.approx(outside, abs=1)


class TestReplacingPieces:
    def test_a_second_piece_on_a_square_replaces_the_first(
        self, editor: LevelEditorScene
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        drag_from_table(editor, "target", cell_pos(editor, 3, 2))

        assert [p.kind for p in editor.pieces] == ["target"]

    def test_a_level_keeps_only_one_laser(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "laser", cell_pos(editor, 0, 0))
        drag_from_table(editor, "laser", cell_pos(editor, 5, 5))

        assert [p.cell for p in editor.pieces] == [(5, 5)]

    def test_a_level_keeps_only_one_target(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "target", cell_pos(editor, 0, 0))
        drag_from_table(editor, "target", cell_pos(editor, 5, 5))

        assert [p.cell for p in editor.pieces] == [(5, 5)]


class TestMovingPlacedPieces:
    def test_a_placed_piece_can_be_dragged_to_another_square(
        self, editor: LevelEditorScene
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()

        press(editor, cell_pos(editor, 3, 2))
        release(editor, cell_pos(editor, 6, 4))

        assert [p.cell for p in editor.pieces] == [(6, 4)]

    def test_dragging_a_placed_piece_back_to_the_table_deletes_it(
        self, editor: LevelEditorScene
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()

        press(editor, cell_pos(editor, 3, 2))
        release(editor, table_pos(editor, "mirror"))

        assert editor.pieces == []

    def test_clicking_a_placed_mirror_opens_the_degree_box(
        self, editor: LevelEditorScene
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()
        where = cell_pos(editor, 3, 2)

        press(editor, where)
        release(editor, (where[0] + CLICK_MOVE_THRESHOLD - 1, where[1]))

        assert isinstance(editor.input_box, InputBox)
        assert [p.cell for p in editor.pieces] == [(3, 2)]

    def test_a_click_on_a_target_leaves_it_alone(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "target", cell_pos(editor, 3, 2))
        editor.draw()

        press(editor, cell_pos(editor, 3, 2))
        release(editor, cell_pos(editor, 3, 2))

        # A target has no angle to set, so no box opens and it stays put
        assert editor.input_box is None
        assert [p.cell for p in editor.pieces] == [(3, 2)]

    def test_the_degree_box_sets_the_mirror_angle(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()
        where = cell_pos(editor, 3, 2)
        press(editor, where)
        release(editor, where)

        type_text(editor, "135")
        key(editor, pygame.K_RETURN)

        assert editor.input_box is None
        assert editor.pieces[0].orientation == 135


class TestSaving:
    def open_dialog(self, editor: LevelEditorScene) -> None:
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

    def build_a_level(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "laser", cell_pos(editor, 0, 2))
        drag_from_table(editor, "target", cell_pos(editor, 4, 0))
        drag_from_table(editor, "mirror", cell_pos(editor, 4, 2))

    def test_the_save_button_opens_the_name_prompt(self, editor: LevelEditorScene) -> None:
        self.open_dialog(editor)

        assert isinstance(editor.dialog, SaveDialog)

    def test_enter_saves_under_the_typed_name(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.build_a_level(editor)
        self.open_dialog(editor)

        type_text(editor, "my level")
        key(editor, pygame.K_RETURN)

        assert editor.dialog is None
        assert (tmp_path / "my_level.toml").exists()

    def test_the_dialog_save_button_saves_too(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.build_a_level(editor)
        self.open_dialog(editor)
        type_text(editor, "clicked")

        assert editor.dialog is not None
        press(editor, editor.dialog.save_button.rect.center)

        assert editor.dialog is None
        assert (tmp_path / "clicked.toml").exists()

    def test_the_saved_file_describes_the_board(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.build_a_level(editor)
        self.open_dialog(editor)
        type_text(editor, "bounce")
        key(editor, pygame.K_RETURN)

        with (tmp_path / "bounce.toml").open("rb") as handle:
            parsed = tomllib.load(handle)

        assert parsed["name"] == "bounce"
        assert parsed["laser"]["cell"] == [0, 2]
        assert parsed["target"]["cell"] == [4, 0]
        assert parsed["mirrors"] == [{"cell": [4, 2], "orientation": 45.0}]

    def test_a_rotated_mirror_is_saved_at_its_angle(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 1, 1))
        editor.draw()
        where = cell_pos(editor, 1, 1)
        press(editor, where)
        release(editor, where)
        type_text(editor, "135")
        key(editor, pygame.K_RETURN)

        self.open_dialog(editor)
        type_text(editor, "angled")
        key(editor, pygame.K_RETURN)

        parsed = tomllib.loads((tmp_path / "angled.toml").read_text())
        assert parsed["mirrors"][0]["orientation"] == 135.0

    def test_escape_cancels_the_prompt_without_saving(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.build_a_level(editor)
        self.open_dialog(editor)
        type_text(editor, "unwanted")

        key(editor, pygame.K_ESCAPE)

        assert editor.dialog is None
        assert list(tmp_path.iterdir()) == []
        assert editor.next_scene is None  # and it did not leave the editor either

    def test_an_empty_name_does_not_save(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.open_dialog(editor)

        key(editor, pygame.K_RETURN)

        assert editor.dialog is not None
        assert list(tmp_path.iterdir()) == []

    def test_saving_reports_where_the_level_landed(self, editor: LevelEditorScene) -> None:
        self.open_dialog(editor)
        type_text(editor, "reported")
        key(editor, pygame.K_RETURN)

        assert "reported.toml" in editor.status

    def test_the_report_fades_after_a_while(self, editor: LevelEditorScene) -> None:
        self.open_dialog(editor)
        type_text(editor, "reported")
        key(editor, pygame.K_RETURN)

        editor.update(60)

        assert editor.status == ""

    def test_an_empty_board_still_saves(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.open_dialog(editor)
        type_text(editor, "empty")
        key(editor, pygame.K_RETURN)

        parsed = tomllib.loads((tmp_path / "empty.toml").read_text())
        assert "laser" not in parsed
        assert "mirrors" not in parsed


class TestResizing:
    def resize(self, editor: LevelEditorScene, width: int, height: int) -> None:
        editor.handle_event(pygame.event.Event(pygame.VIDEORESIZE, {"w": width, "h": height}))

    def test_the_board_re_centers_in_the_new_window(self, editor: LevelEditorScene) -> None:
        self.resize(editor, 1000, 700)

        assert editor.board_rect.right <= editor.table.width
        assert editor.save_button.rect.top >= editor.board_rect.bottom

    def test_placed_pieces_keep_their_squares(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))

        self.resize(editor, 1000, 700)

        assert [p.cell for p in editor.pieces] == [(3, 2)]

    def test_everything_draws_onto_the_new_window(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))

        self.resize(editor, 1000, 700)
        editor.draw()

        assert editor.screen is pygame.display.get_surface()
        assert editor.pieces[0].object.screen is editor.screen


class TestNavigation:
    def test_escape_backs_out_to_the_menu(self, editor: LevelEditorScene) -> None:
        key(editor, pygame.K_ESCAPE)

        assert isinstance(editor.next_scene, MenuScene)

    def test_the_open_degree_box_swallows_escape(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "mirror", cell_pos(editor, 3, 2))
        editor.draw()
        where = cell_pos(editor, 3, 2)
        press(editor, where)
        release(editor, where)

        key(editor, pygame.K_ESCAPE)

        assert editor.input_box is None
        assert editor.next_scene is None

    def test_drawing_a_full_board_does_not_raise(self, editor: LevelEditorScene) -> None:
        for col in range(BOARD_COLS):
            for row in range(BOARD_ROWS):
                drag_from_table(editor, "mirror", cell_pos(editor, col, row))

        editor.draw()

        assert len(editor.pieces) == BOARD_COLS * BOARD_ROWS


class TestLoading:
    """Opening a level that was saved before, editing it, and saving it back
    to the file it came from."""

    def a_level(self, name: str = "Tricky bounce") -> CustomLevel:
        return CustomLevel(
            name=name,
            laser_cell=(0, 2),
            laser_orientation=0.0,
            target_cell=(4, 0),
            mirrors=(MirrorSpec(cell=(4, 2), orientation=135.0),),
        )

    def open_picker(self, editor: LevelEditorScene) -> None:
        press(editor, editor.load_button.rect.center)
        release(editor, editor.load_button.rect.center)

    def pick(self, editor: LevelEditorScene, label: str) -> None:
        self.open_picker(editor)
        assert editor.picker is not None
        for button in editor.picker.buttons:
            if button.label == label:
                press(editor, button.rect.center)
                return
        raise AssertionError(f"no level offered called {label!r}")

    def test_the_load_button_opens_the_list_of_saved_levels(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(self.a_level("one"), tmp_path)
        save(self.a_level("two"), tmp_path)

        self.open_picker(editor)

        assert editor.picker is not None
        assert [b.label for b in editor.picker.buttons] == ["one", "two"]

    def test_loading_with_nothing_saved_says_so(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.open_picker(editor)

        assert editor.picker is None
        assert editor.status == EDITOR_NO_LEVELS_MESSAGE

    def test_picking_a_level_puts_it_on_the_board(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(self.a_level(), tmp_path)

        self.pick(editor, "Tricky bounce")

        assert editor.picker is None
        placed = {(p.kind, p.cell, p.orientation) for p in editor.pieces}
        assert placed == {
            ("laser", (0, 2), 0.0),
            ("target", (4, 0), 0.0),
            ("mirror", (4, 2), 135.0),
        }

    def test_loading_replaces_whatever_was_on_the_board(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(self.a_level(), tmp_path)
        drag_from_table(editor, "mirror", cell_pos(editor, 7, 5))
        drag_from_table(editor, "mirror", cell_pos(editor, 6, 5))

        self.pick(editor, "Tricky bounce")

        assert {p.cell for p in editor.pieces} == {(0, 2), (4, 0), (4, 2)}

    def test_backing_out_leaves_the_board_alone(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(self.a_level(), tmp_path)
        drag_from_table(editor, "mirror", cell_pos(editor, 7, 5))
        self.open_picker(editor)
        assert editor.picker is not None

        press(editor, editor.picker.cancel_button.rect.center)

        assert editor.picker is None
        assert [p.cell for p in editor.pieces] == [(7, 5)]
        assert editor.editing_path is None

    def test_escape_closes_the_list_without_leaving_the_editor(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(self.a_level(), tmp_path)
        self.open_picker(editor)

        key(editor, pygame.K_ESCAPE)

        assert editor.picker is None
        assert editor.next_scene is None

    def test_pieces_that_do_not_fit_this_board_are_left_out(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        # A hand-written file built on a wider board than the game draws
        save(
            CustomLevel(
                name="too wide",
                laser_cell=(0, 2),
                target_cell=(11, 1),
                mirrors=(MirrorSpec(cell=(4, 2), orientation=45.0),),
                cols=12,
                rows=6,
            ),
            tmp_path,
        )

        self.pick(editor, "too wide")

        assert {p.cell for p in editor.pieces} == {(0, 2), (4, 2)}


class TestSavingBackToTheSameFile:
    def build_and_save(self, editor: LevelEditorScene, name: str) -> None:
        drag_from_table(editor, "laser", cell_pos(editor, 0, 2))
        drag_from_table(editor, "target", cell_pos(editor, 4, 0))
        drag_from_table(editor, "mirror", cell_pos(editor, 4, 2))
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)
        type_text(editor, name)
        key(editor, pygame.K_RETURN)

    def test_saving_an_edited_level_writes_the_file_it_came_from(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        loader = TestLoading()
        save(loader.a_level(), tmp_path)
        loader.pick(editor, "Tricky bounce")
        editor.draw()

        # Move the target, then save
        press(editor, cell_pos(editor, 4, 0))
        release(editor, cell_pos(editor, 6, 0))
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

        assert editor.dialog is None, "an already-saved level should not ask for a name again"
        parsed = tomllib.loads((tmp_path / "Tricky_bounce.toml").read_text())
        assert parsed["target"]["cell"] == [6, 0]
        assert parsed["name"] == "Tricky bounce"

    def test_it_does_not_leave_a_second_file_behind(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        loader = TestLoading()
        save(loader.a_level(), tmp_path)
        loader.pick(editor, "Tricky bounce")

        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

        assert [p.name for p in tmp_path.iterdir()] == ["Tricky_bounce.toml"]

    def test_a_file_whose_name_does_not_match_its_level_is_still_the_one_written(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        # Saving by name alone would write "Tricky_bounce.toml" instead
        odd = tmp_path / "renamed_by_hand.toml"
        save_to(TestLoading().a_level(), odd)

        TestLoading().pick(editor, "Tricky bounce")
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

        assert [p.name for p in tmp_path.iterdir()] == ["renamed_by_hand.toml"]

    def test_a_new_level_is_still_asked_to_be_named(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

        assert editor.dialog is not None

    def test_saving_a_second_time_goes_back_to_the_same_file(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        self.build_and_save(editor, "my level")
        editor.draw()

        press(editor, cell_pos(editor, 4, 2))
        release(editor, cell_pos(editor, 5, 3))
        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)

        assert editor.dialog is None
        assert [p.name for p in tmp_path.iterdir()] == ["my_level.toml"]
        parsed = tomllib.loads((tmp_path / "my_level.toml").read_text())
        assert parsed["mirrors"] == [{"cell": [5, 3], "orientation": 45.0}]

    def test_the_footer_names_the_file_being_edited(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(TestLoading().a_level(), tmp_path)

        TestLoading().pick(editor, "Tricky bounce")

        assert "Tricky_bounce.toml" in editor.hint()
        assert "Tricky bounce" in editor.hint()

    def test_a_fresh_editor_explains_itself_instead(self, editor: LevelEditorScene) -> None:
        assert editor.hint() == EDITOR_HINT


class TestWalls:
    """Walls are placed like any other piece, and travel with the level."""

    def test_the_table_offers_a_wall(self, editor: LevelEditorScene) -> None:
        assert "wall" in editor.table.entry_rects

    def test_a_wall_can_be_dragged_onto_the_board(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "wall", cell_pos(editor, 3, 2))

        assert [(p.kind, p.cell) for p in editor.pieces] == [("wall", (3, 2))]

    def test_a_new_wall_stands_upright(self, editor: LevelEditorScene) -> None:
        # So one dropped in front of a laser blocks it straight away
        drag_from_table(editor, "wall", cell_pos(editor, 3, 2))

        assert editor.pieces[0].orientation == 90

    def test_several_walls_can_be_placed(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "wall", cell_pos(editor, 1, 1))
        drag_from_table(editor, "wall", cell_pos(editor, 2, 2))

        assert len(editor.pieces) == 2

    def test_clicking_a_wall_sets_its_angle(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "wall", cell_pos(editor, 3, 2))
        editor.draw()
        where = cell_pos(editor, 3, 2)
        press(editor, where)
        release(editor, where)

        type_text(editor, "30")
        key(editor, pygame.K_RETURN)

        assert editor.pieces[0].orientation == 30

    def test_walls_are_saved_with_the_level(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        drag_from_table(editor, "laser", cell_pos(editor, 0, 2))
        drag_from_table(editor, "target", cell_pos(editor, 7, 2))
        drag_from_table(editor, "mirror", cell_pos(editor, 4, 4))
        drag_from_table(editor, "wall", cell_pos(editor, 4, 2))

        press(editor, editor.save_button.rect.center)
        release(editor, editor.save_button.rect.center)
        type_text(editor, "walled in")
        key(editor, pygame.K_RETURN)

        parsed = tomllib.loads((tmp_path / "walled_in.toml").read_text())
        assert parsed["walls"] == [{"cell": [4, 2], "orientation": 90.0}]
        assert parsed["mirrors"] == [{"cell": [4, 4], "orientation": 45.0}]

    def test_walls_come_back_when_the_level_is_loaded(
        self, editor: LevelEditorScene, tmp_path: Path
    ) -> None:
        save(
            CustomLevel(
                name="walled in",
                laser_cell=(0, 2),
                target_cell=(7, 2),
                mirrors=(MirrorSpec(cell=(4, 4), orientation=45.0),),
                walls=(WallSpec(cell=(4, 2), orientation=90.0),),
            ),
            tmp_path,
        )

        TestLoading().pick(editor, "walled in")

        assert ("wall", (4, 2), 90.0) in {(p.kind, p.cell, p.orientation) for p in editor.pieces}

    def test_a_wall_can_be_dragged_off_the_board_again(self, editor: LevelEditorScene) -> None:
        drag_from_table(editor, "wall", cell_pos(editor, 3, 2))
        editor.draw()

        press(editor, cell_pos(editor, 3, 2))
        release(editor, table_pos(editor, "wall"))

        assert editor.pieces == []
