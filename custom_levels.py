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
from dataclasses import dataclass
from pathlib import Path

from constants import BOARD_COLS, BOARD_ROWS
from levels import Cell, MirrorSpec

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
    """Writes the level out and returns the file it landed in.

    Creates the directory on first use, and overwrites a level saved under
    the same name before.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = path_for(level.name, directory)
    path.write_text(to_toml(level), encoding="utf-8")
    return path


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
