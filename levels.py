from dataclasses import dataclass

# Board coordinates are (column, row), zero-based from the board's top-left.
Cell = tuple[int, int]


@dataclass(frozen=True)
class MirrorSpec:
    cell: Cell
    # Degrees the mirror starts at. 45 is a "/" and 135 a "\", so a level that
    # starts a mirror anywhere else is asking to be rotated into place.
    orientation: float


@dataclass(frozen=True)
class WallSpec:
    cell: Cell
    # Degrees the wall lies at, the same way a mirror's orientation reads:
    # 90 is an upright bar, 0 one lying flat.
    orientation: float


@dataclass(frozen=True)
class LevelLayout:
    number: int
    hint: str
    laser_cell: Cell
    laser_orientation: float  # 0 fires right, 90 fires up
    target_cell: Cell
    mirrors: tuple[MirrorSpec, ...]
    # Obstacles the beam cannot get past. Defaulted, so a level that has none
    # reads exactly as it did before walls existed.
    walls: tuple[WallSpec, ...] = ()


# Beam leaves the laser heading right along row 2 and has to end up on the
# target sitting two rows above the mirror, so the mirror has to become a "/".
LEVEL_ONE = LevelLayout(
    number=1,
    hint="Rotate the mirror until the beam lands on the green target.",
    laser_cell=(0, 2),
    laser_orientation=0,
    target_cell=(4, 0),
    mirrors=(MirrorSpec(cell=(4, 2), orientation=90),),
)

# Every level in play order. Adding an entry here puts a box on the level
# select screen and makes the previous level's "Next Level" button live --
# nothing else needs changing.
LEVELS: list[LevelLayout] = [LEVEL_ONE]


def level_by_number(number: int) -> LevelLayout | None:
    for layout in LEVELS:
        if layout.number == number:
            return layout
    return None


def next_level(current: LevelLayout, levels: list[LevelLayout] | None = None) -> LevelLayout | None:
    # The level after this one, or None if it is the last. Defaults to the
    # built-in set, but a custom set can be handed in to walk that instead.
    pool = LEVELS if levels is None else levels
    for index, layout in enumerate(pool):
        if layout.number == current.number:
            following = pool[index + 1:]
            return following[0] if following else None
    return None
