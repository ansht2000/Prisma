"""Unit tests for the custom level file format: how a typed name becomes a
file name, and that what the editor writes is valid TOML that reads back as
the level that went in.
"""
import tomllib
from pathlib import Path

import pytest

from custom_levels import (
    CustomLevel,
    FALLBACK_FILE_STEM,
    file_stem_for,
    path_for,
    save,
    to_toml,
)
from levels import MirrorSpec

pytestmark = pytest.mark.unit


def make_level(name: str = "Tricky bounce") -> CustomLevel:
    return CustomLevel(
        name=name,
        laser_cell=(0, 2),
        laser_orientation=0.0,
        target_cell=(4, 0),
        mirrors=(MirrorSpec(cell=(4, 2), orientation=45.0),),
    )


def parse(level: CustomLevel) -> dict:
    return tomllib.loads(to_toml(level))


class TestFileStem:
    def test_a_plain_name_is_kept(self) -> None:
        assert file_stem_for("bounce") == "bounce"

    def test_spaces_become_underscores(self) -> None:
        assert file_stem_for("tricky bounce") == "tricky_bounce"

    def test_surrounding_whitespace_is_dropped(self) -> None:
        assert file_stem_for("  bounce  ") == "bounce"

    def test_dashes_and_underscores_survive(self) -> None:
        assert file_stem_for("two-way_split") == "two-way_split"

    def test_path_separators_cannot_escape_the_directory(self) -> None:
        assert "/" not in file_stem_for("../../etc/passwd")
        assert file_stem_for("../../etc/passwd") == "etcpasswd"

    def test_a_name_of_only_punctuation_falls_back(self) -> None:
        assert file_stem_for("***") == FALLBACK_FILE_STEM

    def test_an_empty_name_falls_back(self) -> None:
        assert file_stem_for("   ") == FALLBACK_FILE_STEM

    def test_the_file_is_a_toml_file_in_the_given_directory(self, tmp_path: Path) -> None:
        assert path_for("tricky bounce", tmp_path) == tmp_path / "tricky_bounce.toml"


class TestToToml:
    def test_the_output_is_valid_toml(self) -> None:
        assert isinstance(parse(make_level()), dict)

    def test_the_typed_name_is_kept_verbatim(self) -> None:
        # The file name is sanitised, what the player called the level is not
        assert parse(make_level("Tricky bounce!"))["name"] == "Tricky bounce!"

    def test_quotes_in_a_name_do_not_break_the_file(self) -> None:
        assert parse(make_level('the "hard" one'))["name"] == 'the "hard" one'

    def test_backslashes_in_a_name_do_not_break_the_file(self) -> None:
        assert parse(make_level("back\\slash"))["name"] == "back\\slash"

    def test_the_board_size_is_recorded(self) -> None:
        parsed = parse(make_level())

        assert parsed["board"] == {"cols": 8, "rows": 6}

    def test_the_laser_round_trips(self) -> None:
        parsed = parse(make_level())

        assert parsed["laser"]["cell"] == [0, 2]
        assert parsed["laser"]["orientation"] == 0.0

    def test_the_target_round_trips(self) -> None:
        assert parse(make_level())["target"]["cell"] == [4, 0]

    def test_every_mirror_round_trips(self) -> None:
        level = CustomLevel(
            name="many",
            mirrors=(
                MirrorSpec(cell=(1, 1), orientation=45.0),
                MirrorSpec(cell=(2, 3), orientation=135.0),
            ),
        )

        assert parse(level)["mirrors"] == [
            {"cell": [1, 1], "orientation": 45.0},
            {"cell": [2, 3], "orientation": 135.0},
        ]

    def test_an_orientation_reads_back_as_a_float(self) -> None:
        level = CustomLevel(name="n", mirrors=(MirrorSpec(cell=(0, 0), orientation=90),))

        assert isinstance(parse(level)["mirrors"][0]["orientation"], float)

    def test_a_board_with_no_pieces_still_writes(self) -> None:
        parsed = parse(CustomLevel(name="empty"))

        assert parsed["name"] == "empty"
        assert "laser" not in parsed
        assert "target" not in parsed
        assert "mirrors" not in parsed


class TestSave:
    def test_the_file_lands_in_the_given_directory(self, tmp_path: Path) -> None:
        path = save(make_level(), tmp_path)

        # Case is left alone -- the file is named the way it was typed
        assert path == tmp_path / "Tricky_bounce.toml"
        assert path.exists()

    def test_a_missing_directory_is_created(self, tmp_path: Path) -> None:
        directory = tmp_path / "custom_levels"

        save(make_level(), directory)

        assert directory.is_dir()

    def test_the_written_file_parses_back(self, tmp_path: Path) -> None:
        path = save(make_level(), tmp_path)

        with path.open("rb") as handle:
            parsed = tomllib.load(handle)

        assert parsed["laser"]["cell"] == [0, 2]
        assert parsed["target"]["cell"] == [4, 0]

    def test_saving_the_same_name_twice_overwrites(self, tmp_path: Path) -> None:
        save(make_level(), tmp_path)
        save(
            CustomLevel(name="Tricky bounce", target_cell=(7, 5)),
            tmp_path,
        )

        assert len(list(tmp_path.iterdir())) == 1
        parsed = tomllib.loads((tmp_path / "Tricky_bounce.toml").read_text())
        assert parsed["target"]["cell"] == [7, 5]
