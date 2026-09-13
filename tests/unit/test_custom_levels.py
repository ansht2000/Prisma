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
    SavedLevel,
    load,
    load_all,
    load_all_saved,
    path_for,
    save,
    save_to,
    to_layout,
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


class TestLoad:
    def test_a_saved_level_reads_back_the_same(self, tmp_path: Path) -> None:
        path = save(make_level(), tmp_path)

        assert load(path) == make_level()

    def test_a_level_with_no_pieces_reads_back(self, tmp_path: Path) -> None:
        path = save(CustomLevel(name="empty"), tmp_path)

        assert load(path) == CustomLevel(name="empty")

    def test_a_file_with_no_name_is_known_by_its_file_name(self, tmp_path: Path) -> None:
        path = tmp_path / "nameless.toml"
        path.write_text("[target]\ncell = [1, 1]\n")

        assert load(path).name == "nameless"

    @pytest.mark.parametrize(
        "text",
        [
            "this is not = valid = toml",
            'name = "x"\n[laser]\ncell = "over there"\n',
            'name = "x"\n[laser]\ncell = [1]\n',
            'name = "x"\n[laser]\ncell = [1, 1]\norientation = "sideways"\n',
            'name = "x"\n[target]\ncell = [99, 99]\n',  # off the board
            'name = "x"\n[[mirrors]]\ncell = [-1, 0]\n',
            "name = 12\n",
            'name = "x"\nboard = "big"\n',
        ],
    )
    def test_a_file_that_is_not_a_level_is_rejected(self, tmp_path: Path, text: str) -> None:
        path = tmp_path / "broken.toml"
        path.write_text(text)

        # tomllib's own parse error is a ValueError, so one type covers both
        # a malformed file and a well-formed file holding the wrong things
        with pytest.raises(ValueError):
            load(path)


class TestLoadAll:
    def test_every_saved_level_is_listed(self, tmp_path: Path) -> None:
        save(make_level("one"), tmp_path)
        save(make_level("two"), tmp_path)

        assert [level.name for level in load_all(tmp_path)] == ["one", "two"]

    def test_levels_come_back_in_name_order(self, tmp_path: Path) -> None:
        for name in ("zigzag", "Apple", "middle"):
            save(make_level(name), tmp_path)

        assert [level.name for level in load_all(tmp_path)] == ["Apple", "middle", "zigzag"]

    def test_a_missing_directory_is_empty_rather_than_an_error(self, tmp_path: Path) -> None:
        assert load_all(tmp_path / "never_created") == []

    def test_a_broken_file_does_not_take_the_others_down(self, tmp_path: Path) -> None:
        save(make_level("good"), tmp_path)
        (tmp_path / "broken.toml").write_text("not a level at all = = =")

        assert [level.name for level in load_all(tmp_path)] == ["good"]

    def test_files_that_are_not_levels_are_ignored(self, tmp_path: Path) -> None:
        save(make_level("good"), tmp_path)
        (tmp_path / "notes.txt").write_text("nothing to do with levels")

        assert len(load_all(tmp_path)) == 1


class TestSaveTo:
    def test_it_writes_the_file_it_is_given(self, tmp_path: Path) -> None:
        path = tmp_path / "some_other_name.toml"

        save_to(make_level(), path)

        assert tomllib.loads(path.read_text())["name"] == "Tricky bounce"

    def test_it_ignores_what_the_name_would_have_called_for(self, tmp_path: Path) -> None:
        save_to(make_level(), tmp_path / "kept.toml")

        assert [p.name for p in tmp_path.iterdir()] == ["kept.toml"]

    def test_a_missing_directory_is_created(self, tmp_path: Path) -> None:
        path = tmp_path / "custom_levels" / "deep.toml"

        save_to(make_level(), path)

        assert path.exists()


class TestLoadAllSaved:
    def test_each_level_comes_back_with_its_file(self, tmp_path: Path) -> None:
        written = save(make_level("one"), tmp_path)

        assert load_all_saved(tmp_path) == [SavedLevel(written, make_level("one"))]

    def test_the_file_is_the_real_one_not_one_guessed_from_the_name(
        self, tmp_path: Path
    ) -> None:
        # A file whose name has drifted from the level inside it still reports
        # where it actually lives, which is what saving it again writes to
        save_to(make_level("Tricky bounce"), tmp_path / "renamed_by_hand.toml")

        assert load_all_saved(tmp_path)[0].path == tmp_path / "renamed_by_hand.toml"

    def test_it_agrees_with_load_all(self, tmp_path: Path) -> None:
        for name in ("zigzag", "Apple"):
            save(make_level(name), tmp_path)

        assert [entry.level for entry in load_all_saved(tmp_path)] == load_all(tmp_path)

    def test_a_missing_directory_is_empty(self, tmp_path: Path) -> None:
        assert load_all_saved(tmp_path / "never_created") == []


class TestToLayout:
    def test_a_complete_level_becomes_a_playable_layout(self) -> None:
        layout = to_layout(make_level(), number=3)

        assert layout is not None
        assert layout.number == 3
        assert layout.laser_cell == (0, 2)
        assert layout.target_cell == (4, 0)
        assert layout.mirrors == (MirrorSpec(cell=(4, 2), orientation=45.0),)

    def test_the_level_name_is_shown_as_the_hint(self) -> None:
        layout = to_layout(make_level("Tricky bounce"))

        assert layout is not None
        assert layout.hint == "Tricky bounce"

    def test_a_level_without_a_laser_cannot_be_played(self) -> None:
        assert to_layout(CustomLevel(name="x", target_cell=(4, 0))) is None

    def test_a_level_without_a_target_cannot_be_played(self) -> None:
        assert to_layout(CustomLevel(name="x", laser_cell=(0, 2))) is None

    def test_a_level_with_no_mirrors_cannot_be_played(self) -> None:
        # Nothing for the player to move, so there is no puzzle either way:
        # aimed at the target it would be won on sight, aimed anywhere else it
        # could never be won at all
        no_mirrors = CustomLevel(name="x", laser_cell=(0, 2), target_cell=(4, 0))

        assert to_layout(no_mirrors) is None

    def test_a_level_built_on_another_board_size_cannot_be_played(self) -> None:
        wrong_board = CustomLevel(
            name="x", laser_cell=(0, 2), target_cell=(4, 0), cols=4, rows=4
        )

        assert to_layout(wrong_board) is None
