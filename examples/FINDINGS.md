# What `check-build` found on nine published books

This is the run that produced the `check-build` command. It is recorded here
because the numbers are the argument: these books had passed prose review, had
passed their own structural validators, and had been published and read.

Date: 2026-08-17. Nine books, latest version of each, plus every HTML artifact
in their published sites.

## EPUB

| Result | Count |
|---|---|
| Clean | 8 |
| `epub-responsive-img` + `epub-image-missing`, 15 each | 1 |

The one failure had **every one of its fifteen chapter illustrations rendering
as a blank box.** Not the one the reader happened to notice — all of them.

The build reported success. The project's own EPUB validator reported success,
including a check that every image `src` resolves inside the archive. It did
resolve. The `<img>` also carried a `srcset` left pointing at the web tree, and
reading systems resolve `srcset` first. HTML does not fall back to `src` when
the chosen candidate is missing, so a perfectly valid `src` went unused.

Reproduced by extracting the archive and opening a chapter in WebKit and
Chromium: `naturalWidth` 0, `currentSrc` pointing at a file that is not in the
EPUB. That is the whole defect, and no amount of reading the manuscript finds
it.

## Web pages

| Result | Count |
|---|---|
| Clean | 3 |
| `html-no-text-size-adjust` | 8 |

Eight pages across six books let mobile browsers resize text block by block.
The symptom is specific and confusing: in a table wide enough to scroll
sideways, the long column renders larger than the short ones. The specified CSS
is identical across all of them — same `<td>`, same width, same declared font
size — so the stylesheet cannot explain what you are looking at.

## Why these checks and not others

Each one earned its place by shipping:

- `epub-responsive-img` — the fifteen blank figures above.
- `epub-image-missing` — the same investigation; kept because it is the failure
  the existing validators *did* cover, and a checker that drops it would be a
  downgrade for anyone adopting this one.
- `svg-stretched-corner` — a bar chart whose shortest bar rendered as a pure
  ellipse. A rounded `<rect>` inside `preserveAspectRatio="none"` keeps its
  radius in user units, so each axis stretches it by a different factor. It got
  visibly worse when the reading column was widened from 704px to 1092px —
  distortion went from roughly 4.5:1 to 8:1.
- `html-no-text-size-adjust` — the eight pages above.
- `html-no-viewport` — cheap, and the same class of mobile defect.

## What is checked and still not automated

Pandoc derives table column widths from the **separator row in the markdown**,
not from cell contents. Under `table-layout:fixed`, `|---|---:|---|---|` hands a
two-word column and a full-sentence column the same share. One agenda table had
its short first column at 23% while the long column wrapped to three lines.

There is no check for this, because whether it matters depends on the
renderer's CSS. It is listed in `SKILL.md` as something to look at by eye.

## After the fixes

All eleven artifacts pass. Browsers confirm the mobile rule resolves to `100%`
rather than merely being present in the file, and all fifteen figures render in
the rebuilt EPUB.

The guard is worth more than the fix: the project's EPUB validator now fails on
leftover `srcset`, and that was verified by deliberately disabling the strip and
watching it name all fifteen documents. A check nobody has seen fail is not yet
known to work.
