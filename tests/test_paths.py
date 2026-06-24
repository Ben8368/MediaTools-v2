from pathlib import Path

import pytest

from mediatools.core.paths import is_safe_child, join_under, normalize, relative_to_base


def test_normalize_expands_user_home():
    expanded = normalize("~")
    assert expanded.is_absolute()
    assert expanded == Path.home().resolve()


def test_join_under_preserves_relative_parts(tmp_path):
    base = tmp_path / "workspace"
    joined = join_under(base, "media", "clip.mp4")

    assert joined == base / "media" / "clip.mp4"


def test_relative_to_base_for_nested_file(tmp_path):
    base = tmp_path / "workspace"
    target = base / "media" / "clip.mp4"
    target.parent.mkdir(parents=True)
    target.write_text("demo", encoding="utf-8")

    assert relative_to_base(target, base) == Path("media") / "clip.mp4"


def test_is_safe_child_rejects_path_traversal(tmp_path):
    base = tmp_path / "workspace"
    base.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    sneaky = base / ".." / "outside.txt"

    assert not is_safe_child(sneaky, base)


def test_relative_to_base_raises_for_outside_path(tmp_path):
    base = tmp_path / "workspace"
    base.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(ValueError):
        relative_to_base(outside, base)
