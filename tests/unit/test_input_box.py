"""Unit tests for InputBox: keystroke filtering, commit/cancel behaviour, and
placement. No event loop involved -- events are constructed directly and fed
to handle_event().
"""
import pygame
import pytest

from constants import INPUT_BOX_MAX_CHARS
from input_box import InputBox
from mirror import Mirror

pytestmark = pytest.mark.unit

ARENA_WIDTH = 1066  # matches Table.width for a 1280-wide screen


def key_event(key, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "unicode": unicode})


def click_event(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def type_into(box, text):
    for char in text:
        box.handle_event(key_event(ord(char) if len(char) == 1 else 0, char))


@pytest.fixture
def mirror(screen):
    m = Mirror(400, 300, screen, add_to_groups=False)
    m.draw()
    return m


class TestCommitting:
    def test_enter_commits_and_closes(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)
        type_into(box, "135")

        closed = box.handle_event(key_event(pygame.K_RETURN))

        assert closed is True
        assert mirror.orientation == 135

    def test_click_outside_the_box_commits_and_closes(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)
        type_into(box, "60")
        outside = (box.rect.right + 200, box.rect.bottom + 200)

        closed = box.handle_event(click_event(outside))

        assert closed is True
        assert mirror.orientation == 60

    def test_click_inside_the_box_keeps_it_open(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        closed = box.handle_event(click_event(box.rect.center))

        assert closed is False

    def test_escape_cancels_without_changing_the_target(self, screen, mirror):
        mirror.set_orientation(10)
        box = InputBox(mirror, screen, ARENA_WIDTH)
        type_into(box, "999")

        closed = box.handle_event(key_event(pygame.K_ESCAPE))

        assert closed is True
        assert mirror.orientation == 10

    def test_empty_input_commits_as_a_no_op(self, screen, mirror):
        mirror.set_orientation(33)
        box = InputBox(mirror, screen, ARENA_WIDTH)

        box.handle_event(key_event(pygame.K_RETURN))

        assert mirror.orientation == 33

    def test_lone_minus_sign_commits_as_a_no_op(self, screen, mirror):
        mirror.set_orientation(33)
        box = InputBox(mirror, screen, ARENA_WIDTH)
        type_into(box, "-")

        box.handle_event(key_event(pygame.K_RETURN))

        assert mirror.orientation == 33


class TestKeystrokeFiltering:
    def test_letters_are_rejected(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        type_into(box, "a1b2.5c")

        assert box.text == "12.5"

    def test_leading_minus_sign_is_kept(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        type_into(box, "-45")

        assert box.text == "-45"

    def test_minus_sign_mid_number_is_rejected(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        type_into(box, "4-5")

        assert box.text == "45"

    def test_second_decimal_point_is_rejected(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        type_into(box, "1.2.3")

        assert box.text == "1.23"

    def test_backspace_removes_the_last_character(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)
        type_into(box, "123")

        box.handle_event(key_event(pygame.K_BACKSPACE))

        assert box.text == "12"

    def test_input_is_capped_at_max_chars(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        type_into(box, "1" * (INPUT_BOX_MAX_CHARS + 4))

        assert len(box.text) == INPUT_BOX_MAX_CHARS


class TestPlacement:
    def test_box_stays_within_the_arena(self, screen, mirror):
        box = InputBox(mirror, screen, ARENA_WIDTH)

        assert box.rect.left >= 0
        assert box.rect.right <= ARENA_WIDTH
        assert box.rect.top >= 0
        assert box.rect.bottom <= screen.get_height()

    def test_box_drops_below_the_target_near_the_top_edge(self, screen):
        mirror = Mirror(400, 5, screen, add_to_groups=False)
        mirror.draw()

        box = InputBox(mirror, screen, ARENA_WIDTH)

        assert box.rect.top >= mirror.rect.bottom
