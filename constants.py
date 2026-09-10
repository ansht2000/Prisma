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
