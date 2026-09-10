from abc import ABC, abstractmethod

import pygame


class Scene(ABC):
    # One full-screen mode of the app: the menu, the sandbox, a level, etc.
    #
    # The app loop (see app.py) owns the window, the clock and the event pump.
    # A scene only reacts to events, advances its own state and draws itself.
    # To hand control somewhere else a scene calls go_to() with the scene that
    # should replace it, or request_quit() to close the app. Each frame the app
    # calls handle_event() for every pending event, then update(), then draw().
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self._next_scene: "Scene | None" = None
        self._quit_requested: bool = False

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        ...

    @abstractmethod
    def draw(self) -> None:
        ...

    def go_to(self, scene: "Scene") -> None:
        # Ask the app to swap this scene out for another one after this frame
        self._next_scene = scene

    def request_quit(self) -> None:
        # Ask the app to shut down after this frame
        self._quit_requested = True

    @property
    def next_scene(self) -> "Scene | None":
        return self._next_scene

    @property
    def quit_requested(self) -> bool:
        return self._quit_requested
