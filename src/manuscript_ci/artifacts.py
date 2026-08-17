"""Static checks for built artifacts — EPUB archives and standalone HTML.

`textops.static_check` reads the manuscript. These checks read what the
manuscript was turned into. They catch a class of defect the prose review
cannot see: the text is right, the build is right, the file validates, and
the reader still shows a blank box or a squashed chart.

Every check here comes from a defect that shipped in a real book and was
only found by someone opening the file on their own device.
"""

from __future__ import annotations

import posixpath
import re
import zipfile
from pathlib import PurePosixPath

from .textops import StaticFinding


# Reading systems resolve srcset before src, and HTML does not fall back to
# src when the chosen candidate is missing. EPUB builders that rewrite src to
# the path inside the archive usually leave srcset pointing at the web tree,
# so every figure renders blank while src sits there perfectly valid.
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')

# A rect drawn with rx inside preserveAspectRatio="none" keeps its radius in
# user units, so each axis stretches it by a different factor. The rounded cap
# becomes an ellipse as wide as the container. Bar charts are where this shows.
_SVG_TAG = re.compile(r"<svg\b[^>]*>.*?</svg>", re.IGNORECASE | re.DOTALL)
_ROUNDED_RECT = re.compile(r"<rect\b[^>]*\br[xy]\s*=\s*\"[^\"0][^\"]*\"", re.IGNORECASE)

_XHTML_SUFFIXES = (".xhtml", ".html", ".htm")


def _attrs(tag: str) -> dict[str, str]:
    return {name.lower(): value for name, value in _ATTR.findall(tag)}


def _check_images(label: str, document: str, text: str, members: set[str] | None) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for tag in _IMG_TAG.findall(text):
        attrs = _attrs(tag)
        alt = attrs.get("alt", "")[:40]

        if members is not None:
            leftover = sorted(a for a in ("srcset", "sizes") if a in attrs)
            if leftover:
                findings.append(
                    StaticFinding(
                        "epub-responsive-img",
                        label,
                        f"{document}: {'/'.join(leftover)} on <img alt=\"{alt}\"> — "
                        "readers prefer srcset and will not fall back to src",
                    )
                )

            src = attrs.get("src", "")
            if not src:
                findings.append(
                    StaticFinding("epub-image-no-src", label, f"{document}: <img> without src")
                )
            elif not src.startswith(("http://", "https://", "data:")):
                resolved = posixpath.normpath(
                    posixpath.join(str(PurePosixPath(document).parent), src)
                )
                if resolved not in members:
                    findings.append(
                        StaticFinding(
                            "epub-image-missing",
                            label,
                            f"{document}: src={src} is not in the archive",
                        )
                    )
    return findings


def _check_svg(label: str, document: str, text: str) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for svg in _SVG_TAG.findall(text):
        if 'preserveaspectratio="none"' not in svg.lower():
            continue
        rounded = _ROUNDED_RECT.findall(svg)
        if rounded:
            findings.append(
                StaticFinding(
                    "svg-stretched-corner",
                    label,
                    f"{document}: {len(rounded)} rounded rect(s) inside "
                    'preserveAspectRatio="none" — the radius stretches with the '
                    "container and renders as an ellipse",
                )
            )
    return findings


def _check_html_page(label: str, text: str) -> list[StaticFinding]:
    """Checks that only make sense for a page a browser loads directly."""
    findings: list[StaticFinding] = []
    head = text[:4000].lower()

    if "<meta" in head and "viewport" not in head:
        findings.append(
            StaticFinding(
                "html-no-viewport",
                label,
                "no viewport meta — mobile browsers assume a desktop width",
            )
        )

    # Mobile Safari inflates text by how wide its block is relative to the
    # viewport. In a table that scrolls sideways the long column grows and the
    # short ones do not, so one table renders at two different sizes.
    if "text-size-adjust" not in text.lower():
        findings.append(
            StaticFinding(
                "html-no-text-size-adjust",
                label,
                "no text-size-adjust — mobile browsers may resize text per block",
            )
        )
    return findings


def check_epub(path) -> list[StaticFinding]:
    label = str(path)
    if not zipfile.is_zipfile(path):
        return [StaticFinding("epub-unreadable", label, "not a zip archive")]

    findings: list[StaticFinding] = []
    with zipfile.ZipFile(path) as archive:
        members = set(archive.namelist())
        documents = sorted(n for n in members if n.lower().endswith(_XHTML_SUFFIXES))
        if not documents:
            return [StaticFinding("epub-empty", label, "no XHTML documents inside")]

        for name in documents:
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                findings.append(
                    StaticFinding("epub-encoding", label, f"{name}: not valid UTF-8")
                )
                continue
            findings.extend(_check_images(label, name, text, members))
            findings.extend(_check_svg(label, name, text))
    return findings


def check_html(path) -> list[StaticFinding]:
    label = str(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = _check_html_page(label, text)
    findings.extend(_check_svg(label, path.name, text))
    return findings


def artifact_check(paths) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".epub":
            findings.extend(check_epub(path))
        elif suffix in _XHTML_SUFFIXES:
            findings.extend(check_html(path))
        else:
            findings.append(
                StaticFinding(
                    "unsupported-artifact",
                    str(path),
                    f"{suffix or 'no suffix'} — expected .epub, .html, or .xhtml",
                )
            )
    return findings
