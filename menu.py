from dataclasses import dataclass
from typing import Callable

import pygame

from button import Button
from constants import *
from render_utils import render_text
from scene import Scene

# What a menu entry does when clicked. It receives the menu itself, so an
# action can swap in another scene (menu.go_to(...)), close the app
# (menu.request_quit()), or do anything else a screen can do.
MenuAction = Callable[["MenuScene"], None]


@dataclass(frozen=True)
class MenuOption:
    label: str
    action: MenuAction
    # Listed but unclickable -- drawn dimmed, ignores clicks
    enabled: bool = True


def start_sandbox(menu: "MenuScene") -> None:
    # Local import: sandbox.py imports this module back for its "escape to
    # menu" key, so importing it at module scope would be circular
    from sandbox import SandboxScene

    menu.go_to(SandboxScene(menu.screen))


def open_level_select(menu: "MenuScene") -> None:
    # Local import for the same reason as start_sandbox above
    from level_select import LevelSelectScene

    menu.go_to(LevelSelectScene(menu.screen))


def open_level_editor(menu: "MenuScene") -> None:
    # Local import for the same reason as start_sandbox above
    from level_editor import LevelEditorScene

    menu.go_to(LevelEditorScene(menu.screen))


def quit_game(menu: "MenuScene") -> None:
    menu.request_quit()


def not_built_yet(menu: "MenuScene") -> None:
    # Placeholder for options that are listed but have no screen behind them
    # yet. Swap this for a real action (and flip enabled=True) when there is
    # something to open.
    pass


# The menu is built from this list, in order. Add, remove or reorder entries
# here and the screen lays itself out to match -- nothing else needs touching.
MENU_OPTIONS: list[MenuOption] = [
    MenuOption("Sandbox", start_sandbox),
    MenuOption("Level Select", open_level_select),
    MenuOption("Level Editor", open_level_editor),
    MenuOption("Settings", not_built_yet, enabled=False),
    MenuOption("Quit", quit_game),
]


class MenuScene(Scene):
    # The title screen. Owns no game state -- it just turns MENU_OPTIONS into
    # clickable buttons and runs the matching action.
    def __init__(self, screen: pygame.Surface, options: list[MenuOption] | None = None) -> None:
        super().__init__(screen)
        # Injectable so a test (or a future sub-menu) can supply its own set
        self.options: list[MenuOption] = MENU_OPTIONS if options is None else options
        self.title_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_TITLE_FONT_SIZE)
        self.button_font: pygame.font.Font = pygame.font.SysFont("Arial", MENU_BUTTON_FONT_SIZE)
        self.buttons: list[Button] = []
        self.title_center: tuple[float, float] = (0, 0)
        self._layout()

    def _layout(self) -> None:
        # Stack the buttons in a centered column, with the title above them
        width = self.screen.get_width()
        height = self.screen.get_height()
        count = len(self.options)
        block_height = (
            count * MENU_BUTTON_HEIGHT + max(count - 1, 0) * MENU_BUTTON_SPACING
        )
        # Nudge the block below center so the title has room without overlapping
        block_top = (height - block_height) // 2 + MENU_TITLE_GAP // 2
        left = (width - MENU_BUTTON_WIDTH) // 2

        self.buttons = [
            Button(
                option.label,
                pygame.Rect(
                    left,
                    block_top + index * (MENU_BUTTON_HEIGHT + MENU_BUTTON_SPACING),
                    MENU_BUTTON_WIDTH,
                    MENU_BUTTON_HEIGHT,
                ),
                self.button_font,
                option.enabled,
            )
            for index, option in enumerate(self.options)
        ]
        self.title_center = (width // 2, max(block_top - MENU_TITLE_GAP, MENU_TITLE_FONT_SIZE))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._layout()
            return

        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.hovered = button.contains(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for option, button in zip(self.options, self.buttons):
                if button.enabled and button.contains(event.pos):
                    option.action(self)
                    return

    def update(self, dt: float) -> None:
        # Nothing to advance over time; the menu is entirely event driven
        pass

    def draw(self) -> None:
        self.screen.fill("black")

        title_text, title_rect = render_text(
            self.title_font, MENU_TITLE, MENU_ENABLED_COLOR, self.title_center
        )
        self.screen.blit(title_text, title_rect)

        for button in self.buttons:
            button.draw(self.screen)
