from pathlib import Path

import pytest

from manuscript_ci.textops import apply_exact_once, static_check


def test_apply_exact_once():
    assert apply_exact_once("alpha beta", "beta", "gamma") == "alpha gamma"


def test_apply_rejects_ambiguous_find():
    with pytest.raises(ValueError):
        apply_exact_once("x x", "x", "y")


def test_static_check_finds_cross_file_duplicate(tmp_path: Path):
    paragraph = "This is a sufficiently long repeated paragraph. " * 4
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(paragraph, encoding="utf-8")
    b.write_text(paragraph, encoding="utf-8")
    findings = static_check([a, b])
    assert any(item.kind == "duplicate-across-files" for item in findings)
