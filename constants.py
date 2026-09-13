# Constants for padding, distances, etc.
PADDING_TOP: int = 30
MARKING_OFFSET: int = 10
OBJECT_PADDING: int = 60  # gap above each object in the table
OBJECT_LABEL_GAP: int = 22  # from an object's bottom to the middle of its name
OBJECT_DIVIDER_GAP: int = 14  # from a name to the line closing off its entry
TITLE_FONT_SIZE: int = 36
OBJECT_FONT_SIZE: int = 24
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
MIRROR_DEFAULT_SIZE: int = 100
ROTATION_SPEED: int = 90
# Holding shift turns a piece at 30% less than full speed, for fine aiming
SLOW_ROTATION_FACTOR: float = 0.7

# How big a piece is drawn, everywhere it appears: on a level board, in the
# editor, in the sandbox, and as the sample in the objects table
MIRROR_LENGTH: int = 60
LASER_LENGTH: int = 60
WALL_LENGTH: int = 60

# Walls: drawn like a mirror, but thicker and grey, and the beam stops dead
# at one instead of bouncing off it
WALL_COLOR: tuple[int, int, int] = (130, 130, 130)
WALL_WIDTH: int = 14
MIRROR_WIDTH: int = 5

# Degree-entry box
CLICK_MOVE_THRESHOLD: int = 5  # px of travel below which a press/release counts as a click, not a drag
INPUT_BOX_WIDTH: int = 180
INPUT_BOX_HEIGHT: int = 72
INPUT_BOX_MARGIN: int = 12
INPUT_BOX_FONT_SIZE: int = 26
INPUT_BOX_LABEL_FONT_SIZE: int = 18
INPUT_BOX_MAX_CHARS: int = 8

# Menu screen
MENU_TITLE: str = "Prisma"
MENU_TITLE_FONT_SIZE: int = 72
MENU_BUTTON_FONT_SIZE: int = 32
MENU_BUTTON_WIDTH: int = 320
MENU_BUTTON_HEIGHT: int = 64
MENU_BUTTON_SPACING: int = 20
MENU_TITLE_GAP: int = 70  # vertical gap between the title and the first button
MENU_BUTTON_FILL: tuple[int, int, int] = (28, 28, 28)
MENU_BUTTON_HOVER_FILL: tuple[int, int, int] = (64, 64, 64)
MENU_BORDER_WIDTH: int = 2
MENU_ENABLED_COLOR: tuple[int, int, int] = (255, 255, 255)
MENU_DISABLED_COLOR: tuple[int, int, int] = (110, 110, 110)
MENU_SPLIT_GAP: int = 12  # space between the halves of an entry that splits on hover

# Level select screens
LEVEL_SELECT_TITLE: str = "Level Select"
LEVEL_BOX_SIZE: int = 80
LEVEL_BOX_MARGIN: int = 30  # gap from the screen edges
LEVEL_BOX_SPACING: int = 16
LEVEL_BOX_FONT_SIZE: int = 40
LEVEL_TITLE_GAP: int = 24  # gap between the heading and the first row of boxes

# Custom level select screen. Boxes are labelled with the name the player
# gave the level rather than a number, so they are wider and lettered smaller.
CUSTOM_SELECT_TITLE: str = "Custom Levels"
CUSTOM_BOX_WIDTH: int = 210
CUSTOM_BOX_FONT_SIZE: int = 22
CUSTOM_EMPTY_MESSAGE: str = "No custom levels yet -- build one in the Level Editor."
CUSTOM_EMPTY_FONT_SIZE: int = 24
CUSTOM_EMPTY_COLOR: tuple[int, int, int] = (150, 150, 150)

# Levels
BOARD_COLS: int = 8
BOARD_ROWS: int = 6
BOARD_CELL_SIZE: int = 90
BOARD_LIGHT_CELL: tuple[int, int, int] = (34, 34, 34)
BOARD_DARK_CELL: tuple[int, int, int] = (22, 22, 22)
BOARD_GRID_COLOR: tuple[int, int, int] = (70, 70, 70)
LEVEL_HINT_FONT_SIZE: int = 20
# Shown in place of a level's own hint when its beam is already on the target
# but the player has not moved anything yet, so the board is not just sitting
# there looking solved and silent
LEVEL_UNTOUCHED_HINT: str = "Move a mirror to finish the level."
LEVEL_HINT_COLOR: tuple[int, int, int] = (150, 150, 150)
TARGET_SIZE: int = 46
TARGET_BORDER_WIDTH: int = 4
TARGET_COLOR: tuple[int, int, int] = (60, 200, 90)
# A target has to be held in the beam rather than merely touched by it: it
# fills with this colour from the bottom up, and the level is won once full
TARGET_CHARGE_COLOR: tuple[int, int, int] = (220, 60, 60)
TARGET_CHARGE_SECONDS: float = 3.0

# Overlay panel (used by the win screen)
OVERLAY_TITLE_FONT_SIZE: int = 56
OVERLAY_PADDING: int = 40
OVERLAY_TITLE_GAP: int = 40
OVERLAY_DIM_ALPHA: int = 190  # how strongly the overlay dims the scene behind it
OVERLAY_PANEL_FILL: tuple[int, int, int] = (18, 18, 18)
LEVEL_WIN_TITLE: str = "You win!"

# Level editor
EDITOR_SAVE_LABEL: str = "Save"
EDITOR_LOAD_LABEL: str = "Load"
EDITOR_BUTTON_GAP: int = 16  # space between the save and load buttons
EDITOR_SAVE_BUTTON_WIDTH: int = 160
EDITOR_SAVE_BUTTON_HEIGHT: int = 48
EDITOR_SAVE_FONT_SIZE: int = 26
EDITOR_BOARD_GAP: int = 24  # vertical gap between the board and the save button
EDITOR_BOARD_TOP_MIN: int = 20  # smallest gap between the board and the screen top
EDITOR_STATUS_FONT_SIZE: int = 18
EDITOR_STATUS_COLOR: tuple[int, int, int] = (150, 200, 150)
EDITOR_STATUS_SECONDS: float = 4.0  # how long a "saved" message stays up
EDITOR_NO_LEVELS_MESSAGE: str = "No custom levels saved yet."
# Shown while the editor is working on a level that already has a file, so it
# is clear that saving updates that file rather than asking for a new name
EDITOR_EDITING_HINT: str = 'Editing "{name}" -- Save writes back to {file}'

# Load dialog (the list of levels the editor can open)
LOAD_DIALOG_TITLE: str = "Load Level"
LOAD_DIALOG_CANCEL_LABEL: str = "Cancel"

# Name-entry dialog (used when saving a custom level)
NAME_DIALOG_TITLE: str = "Level name"
NAME_DIALOG_WIDTH: int = 420
NAME_DIALOG_PADDING: int = 24
NAME_DIALOG_FIELD_HEIGHT: int = 48
NAME_DIALOG_BUTTON_WIDTH: int = 140
NAME_DIALOG_BUTTON_HEIGHT: int = 44
NAME_DIALOG_GAP: int = 18
NAME_DIALOG_FONT_SIZE: int = 26
NAME_DIALOG_LABEL_FONT_SIZE: int = 20
NAME_DIALOG_MAX_CHARS: int = 32
NAME_DIALOG_FILL: tuple[int, int, int] = (20, 20, 20)
NAME_DIALOG_FIELD_FILL: tuple[int, int, int] = (10, 10, 10)
NAME_DIALOG_LABEL_COLOR: tuple[int, int, int] = (180, 180, 180)
