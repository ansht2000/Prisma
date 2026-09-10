from typing import Callable

import pygame

from constants import *
from scene import Scene

# Builds the scene to start on, given the window surface
SceneFactory = Callable[[pygame.Surface], Scene]


def run(initial_scene: SceneFactory) -> None:
    # Owns the window, the clock and the event pump, and swaps between scenes
    # as they ask to hand over. Which scene it starts on is a parameter so the
    # app can boot into the menu while a test can boot straight into a mode.
    pygame.init()
    pygame.display.set_caption("Prisma")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    scene: Scene = initial_scene(screen)
    running = True
    dt: float = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            scene.handle_event(event)

        if not running:
            break

        scene.update(dt)

        if scene.quit_requested:
            break
        if scene.next_scene is not None:
            scene = scene.next_scene

        scene.draw()
        pygame.display.flip()
        dt = clock.tick(60) / 1000

    pygame.quit()
