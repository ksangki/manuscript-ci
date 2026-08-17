import zipfile
from pathlib import Path

from manuscript_ci.artifacts import artifact_check


FIGURE = (
    '<figure><img srcset="assets/images/fig-704.webp 704w, assets/images/fig.webp 1408w" '
    'sizes="(max-width: 736px) 100vw, 704px" src="../media/file0.webp" '
    'alt="a chart" width="1408" height="939" /></figure>'
)

BAR = (
    '<svg class="bar" viewBox="0 0 100 10" preserveAspectRatio="none">'
    '<rect x="0" y="0" width="100" height="10" rx="5" />'
    '<rect x="0" y="0" width="28" height="10" rx="5" /></svg>'
)


def _epub(path: Path, body: str, extra: dict[str, bytes] | None = None) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("EPUB/text/ch001.xhtml", f"<html><body>{body}</body></html>")
        for name, blob in (extra or {}).items():
            archive.writestr(name, blob)
    return path


def test_flags_srcset_that_readers_prefer_over_src(tmp_path: Path):
    book = _epub(tmp_path / "b.epub", FIGURE, {"EPUB/media/file0.webp": b"x"})
    kinds = {f.kind for f in artifact_check([book])}
    assert "epub-responsive-img" in kinds
    # src itself resolves, which is exactly why the defect is easy to miss
    assert "epub-image-missing" not in kinds


def test_flags_src_that_is_not_in_the_archive(tmp_path: Path):
    book = _epub(tmp_path / "b.epub", '<img src="../media/gone.webp" alt="x" />')
    findings = artifact_check([book])
    assert any(f.kind == "epub-image-missing" for f in findings)


def test_clean_epub_has_no_findings(tmp_path: Path):
    book = _epub(
        tmp_path / "b.epub",
        '<img src="../media/file0.webp" alt="a chart" />',
        {"EPUB/media/file0.webp": b"x"},
    )
    assert artifact_check([book]) == []


def test_flags_rounded_rect_under_non_uniform_scaling(tmp_path: Path):
    book = _epub(tmp_path / "b.epub", BAR)
    findings = artifact_check([book])
    assert any(f.kind == "svg-stretched-corner" for f in findings)


def test_square_rect_under_non_uniform_scaling_is_fine(tmp_path: Path):
    squared = BAR.replace(' rx="5"', "")
    book = _epub(tmp_path / "b.epub", squared)
    assert not any(f.kind == "svg-stretched-corner" for f in artifact_check([book]))


def test_rounded_rect_is_fine_when_scaling_is_uniform(tmp_path: Path):
    uniform = BAR.replace(' preserveAspectRatio="none"', "")
    book = _epub(tmp_path / "b.epub", uniform)
    assert not any(f.kind == "svg-stretched-corner" for f in artifact_check([book]))


def test_html_without_text_size_adjust_is_flagged(tmp_path: Path):
    page = tmp_path / "index.html"
    page.write_text(
        '<html><head><meta name="viewport" content="width=device-width" />'
        "<style>body{font-size:17px}</style></head><body><p>hi</p></body></html>",
        encoding="utf-8",
    )
    kinds = {f.kind for f in artifact_check([page])}
    assert "html-no-text-size-adjust" in kinds
    assert "html-no-viewport" not in kinds


def test_html_with_both_guards_is_clean(tmp_path: Path):
    page = tmp_path / "index.html"
    page.write_text(
        '<html><head><meta name="viewport" content="width=device-width" />'
        "<style>html{-webkit-text-size-adjust:100%}</style></head>"
        "<body><p>hi</p></body></html>",
        encoding="utf-8",
    )
    assert artifact_check([page]) == []


def test_unknown_suffix_is_reported_rather_than_ignored(tmp_path: Path):
    other = tmp_path / "notes.md"
    other.write_text("text", encoding="utf-8")
    findings = artifact_check([other])
    assert [f.kind for f in findings] == ["unsupported-artifact"]
