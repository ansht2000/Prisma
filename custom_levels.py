"""Reading and writing the files the level editor produces.

The format is TOML: Python parses it out of the standard library (tomllib,
no extra dependency), and a level is mostly a handful of named scalars plus a
repeated piece -- which TOML's array-of-tables ([[mirrors]]) says directly.

A saved level looks like this:

    name = "Tricky bounce"

    [board]
    cols = 8
    rows = 6

    [laser]
    cell = [0, 2]
    orientation = 0.0

    [target]
    cell = [4, 0]

    [[mirrors]]
    cell = [4, 2]
    orientation = 90.0
"""
import tomllib
from dataclasses import dataclass
from pathlib import Path

from constants import BOARD_COLS, BOARD_ROWS
from levels import Cell, LevelLayout, MirrorSpec

# Levels the editor saves live here, next to the game rather than next to
# whatever directory the game happened to be started from.
CUSTOM_LEVELS_DIR: Path = Path(__file__).resolve().parent / "custom_levels"

FILE_EXTENSION: str = ".toml"
# Used when a name sanitises down to nothing at all (say, "***")
FALLBACK_FILE_STEM: str = "level"


@dataclass(frozen=True)
class CustomLevel:
    # A level as the editor has it: the board, whatever pieces have been put
    # on it, and the name the player typed. The laser and the target are
    # optional because the editor lets a half-finished board be saved.
    name: str
    laser_cell: Cell | None = None
    laser_orientation: float = 0.0
    target_cell: Cell | None = None
    mirrors: tuple[MirrorSpec, ...] = ()
    cols: int = BOARD_COLS
    rows: int = BOARD_ROWS


@dataclass(frozen=True)
class SavedLevel:
    # A level together with the file it came from, so that editing one and
    # saving it again can go back to the same file
    path: Path
    level: CustomLevel


def file_stem_for(name: str) -> str:
    """The file name (without extension) a typed level name is saved under.

    Everything that is not a letter, digit, dash or underscore is dropped and
    runs of whitespace become underscores, so a name can never walk out of the
    custom levels directory or collide with a path separator.
    """
    cleaned: list[str] = []
    for char in name.strip():
        if char.isalnum() or char in "-_":
            cleaned.append(char)
        elif char.isspace():
            cleaned.append("_")
    stem = "".join(cleaned).strip("_")
    return stem or FALLBACK_FILE_STEM


def path_for(name: str, directory: Path = CUSTOM_LEVELS_DIR) -> Path:
    return directory / (file_stem_for(name) + FILE_EXTENSION)


def to_toml(level: CustomLevel) -> str:
    lines: list[str] = [
        "# Prisma custom level, written by the in-game level editor.",
        f"name = {_toml_string(level.name)}",
        "",
        "[board]",
        f"cols = {level.cols}",
        f"rows = {level.rows}",
    ]

    if level.laser_cell is not None:
        lines += [
            "",
            "[laser]",
            f"cell = {_toml_cell(level.laser_cell)}",
            f"orientation = {_toml_float(level.laser_orientation)}",
        ]

    if level.target_cell is not None:
        lines += [
            "",
            "[target]",
            f"cell = {_toml_cell(level.target_cell)}",
        ]

    for mirror in level.mirrors:
        lines += [
            "",
            "[[mirrors]]",
            f"cell = {_toml_cell(mirror.cell)}",
            f"orientation = {_toml_float(mirror.orientation)}",
        ]

    return "\n".join(lines) + "\n"


def save(level: CustomLevel, directory: Path = CUSTOM_LEVELS_DIR) -> Path:
    """Writes the level to the file its name calls for, and returns it.

    Creates the directory on first use, and overwrites a level saved under
    the same name before.
    """
    return save_to(level, path_for(level.name, directory))


def save_to(level: CustomLevel, path: Path) -> Path:
    """Writes the level to one particular file, whatever it is called.

    This is what editing an existing level saves through: the file it was
    loaded from, rather than whatever its name would otherwise pick.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_toml(level), encoding="utf-8")
    return path


def load(path: Path) -> CustomLevel:
    """Reads one saved level back.

    Raises ValueError if the file is not the shape this module writes --
    tomllib's own parse error is a ValueError too, so a caller only has to
    watch for that one type.
    """
    with path.open("rb") as handle:
        parsed = tomllib.load(handle)

    board = _table(parsed.get("board", {}), "board")
    cols = _int(board.get("cols", BOARD_COLS), "board.cols")
    rows = _int(board.get("rows", BOARD_ROWS), "board.rows")

    laser_cell: Cell | None = None
    laser_orientation = 0.0
    if "laser" in parsed:
        laser = _table(parsed["laser"], "laser")
        laser_cell = _cell(laser.get("cell"), "laser.cell", cols, rows)
        laser_orientation = _float(laser.get("orientation", 0.0), "laser.orientation")

    target_cell: Cell | None = None
    if "target" in parsed:
        target = _table(parsed["target"], "target")
        target_cell = _cell(target.get("cell"), "target.cell", cols, rows)

    mirrors: list[MirrorSpec] = []
    for index, entry in enumerate(parsed.get("mirrors", [])):
        mirror = _table(entry, f"mirrors[{index}]")
        mirrors.append(
            MirrorSpec(
                cell=_cell(mirror.get("cell"), f"mirrors[{index}].cell", cols, rows),
                orientation=_float(
                    mirror.get("orientation", 0.0), f"mirrors[{index}].orientation"
                ),
            )
        )

    # A file with no name of its own is known by the file it lives in
    name = parsed.get("name", path.stem)
    if not isinstance(name, str):
        raise ValueError("name must be text")

    return CustomLevel(
        name=name,
        laser_cell=laser_cell,
        laser_orientation=laser_orientation,
        target_cell=target_cell,
        mirrors=tuple(mirrors),
        cols=cols,
        rows=rows,
    )


def load_all_saved(directory: Path = CUSTOM_LEVELS_DIR) -> list[SavedLevel]:
    """Every level saved in the directory, in name order, with its file.

    A file that cannot be read -- hand-edited into nonsense, or not a level at
    all -- is left out rather than taking the whole list down with it.
    """
    if not directory.is_dir():
        return []

    saved: list[SavedLevel] = []
    for path in sorted(directory.glob("*" + FILE_EXTENSION)):
        try:
            saved.append(SavedLevel(path, load(path)))
        except (OSError, ValueError):
            continue
    return sorted(saved, key=lambda entry: entry.level.name.lower())


def load_all(directory: Path = CUSTOM_LEVELS_DIR) -> list[CustomLevel]:
    """Every level saved in the directory, in name order."""
    return [entry.level for entry in load_all_saved(directory)]


def to_layout(level: CustomLevel, number: int = 1) -> LevelLayout | None:
    """The level as something LevelScene can play, or None if it cannot be.

    A level saved without a laser or without a target has nothing to solve,
    one with no mirrors has nothing the player can move, and one built on a
    differently sized board would not fit the one the game draws -- in each
    case there is no puzzle to play.
    """
    if level.laser_cell is None or level.target_cell is None:
        return None
    if not level.mirrors:
        return None
    if (level.cols, level.rows) != (BOARD_COLS, BOARD_ROWS):
        return None
    return LevelLayout(
        number=number,
        hint=level.name,
        laser_cell=level.laser_cell,
        laser_orientation=level.laser_orientation,
        target_cell=level.target_cell,
        mirrors=level.mirrors,
    )


# -- TOML value reading ----------------------------------------------------


def _table(value: object, where: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be a table")
    return value


def _int(value: object, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{where} must be a whole number")
    return value


def _float(value: object, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{where} must be a number")
    return float(value)


def _cell(value: object, where: str, cols: int, rows: int) -> Cell:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{where} must be a pair of numbers")
    col = _int(value[0], where)
    row = _int(value[1], where)
    if not (0 <= col < cols and 0 <= row < rows):
        raise ValueError(f"{where} is off the board")
    return (col, row)


# -- TOML value formatting -------------------------------------------------
# Only the handful of value shapes this format uses, rather than a general
# writer: a level is a name, some integers and some pairs of them.


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _toml_cell(cell: Cell) -> str:
    return f"[{cell[0]}, {cell[1]}]"


def _toml_float(value: float) -> str:
    # repr() of a float always keeps the decimal point, so an orientation of
    # 90 reads back as the float 90.0 rather than as an integer
    return repr(float(value))
