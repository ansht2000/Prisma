# Constants for padding, distances, etc.
PADDING_TOP: int = 30
MARKING_OFFSET: int = 10
OBJECT_PADDING: int = 60
TITLE_FONT_SIZE: int = 36
OBJECT_FONT_SIZE: int = 24
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
MIRROR_DEFAULT_SIZE: int = 100
ROTATION_SPEED: int = 90

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

# Level select screen
LEVEL_SELECT_TITLE: str = "Level Select"
LEVEL_BOX_SIZE: int = 80
LEVEL_BOX_MARGIN: int = 30  # gap from the screen edges
LEVEL_BOX_SPACING: int = 16
LEVEL_BOX_FONT_SIZE: int = 40

# Levels
BOARD_COLS: int = 8
BOARD_ROWS: int = 6
BOARD_CELL_SIZE: int = 90
BOARD_LIGHT_CELL: tuple[int, int, int] = (34, 34, 34)
BOARD_DARK_CELL: tuple[int, int, int] = (22, 22, 22)
BOARD_GRID_COLOR: tuple[int, int, int] = (70, 70, 70)
LEVEL_MIRROR_LENGTH: int = 60
LEVEL_LASER_LENGTH: int = 60
LEVEL_HINT_FONT_SIZE: int = 20
LEVEL_HINT_COLOR: tuple[int, int, int] = (150, 150, 150)
TARGET_SIZE: int = 46
TARGET_COLOR: tuple[int, int, int] = (60, 200, 90)
TARGET_HIT_COLOR: tuple[int, int, int] = (255, 220, 80)

# Overlay panel (used by the win screen)
OVERLAY_TITLE_FONT_SIZE: int = 56
OVERLAY_PADDING: int = 40
OVERLAY_TITLE_GAP: int = 40
OVERLAY_DIM_ALPHA: int = 190  # how strongly the overlay dims the scene behind it
OVERLAY_PANEL_FILL: tuple[int, int, int] = (18, 18, 18)
LEVEL_WIN_TITLE: str = "You win!"

# Level editor
EDITOR_SAVE_LABEL: str = "Save"
EDITOR_SAVE_BUTTON_WIDTH: int = 160
EDITOR_SAVE_BUTTON_HEIGHT: int = 48
EDITOR_SAVE_FONT_SIZE: int = 26
EDITOR_BOARD_GAP: int = 24  # vertical gap between the board and the save button
EDITOR_BOARD_TOP_MIN: int = 20  # smallest gap between the board and the screen top
EDITOR_STATUS_FONT_SIZE: int = 18
EDITOR_STATUS_COLOR: tuple[int, int, int] = (150, 200, 150)
EDITOR_STATUS_SECONDS: float = 4.0  # how long a "saved" message stays up

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
