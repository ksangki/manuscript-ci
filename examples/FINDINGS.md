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

## The prose pass, over the same nine books

`check-build` covers the artifact. This is what `check` — the manuscript pass —
reported over 130 chapter files.

| Finding | Count |
|---|---|
| `duplicate-across-files` | 4 |
| `duplicate-within-file` | 2 |
| `short-file` | 0 |
| `strong-claim-word` | 419 |

### The duplicates are decisions, not defects

All four cross-file duplicates are a **quotation reused in two chapters** — an
external quote in a prologue and again in the chapter that argues from it, or in
an appendix that collects quotes. The two within-file duplicates are a code
listing shown twice in a hands-on chapter, once in part and once in full.

None is obviously wrong. Every one is a call only the author can make, which is
why `check` exits zero and `check-build` does not.

### Getting the file list wrong invents findings

The first run reported **121 cross-file duplicates** in one book. Every one was
an artifact of the invocation: `chapters/*.md` picked up both `01_chapter1.md`
and `01_final.md`, superseded copies sitting beside the live ones. Two of the
pairs were byte-identical.

Re-running on the canonical set gave zero. The lesson generalizes — pass the
files the book is actually built from, or the duplicate checks will report your
directory layout back to you as an editorial problem.

### `strong-claim-word` needs reading, not acting

419 hits, and they are dominated by ordinary Korean quantifiers: 모두 (149),
대부분 (87), 반드시 (73), 전부 (59).

Of these, 6% sit inside quoted material, 5% are inside a hedge that means the
*opposite* of an overclaim (`반드시 … 은 아니다`), and 2% are in code blocks,
tables, or headings. Twelve body-prose hits were sampled and read: none was an
unsupported factual claim. They were deliberate instructions ("반드시 담당자가
검토하도록"), plain quantifiers ("모두가 배울 수 있는"), and narration ("전부
짰다").

The check is a lexical flag, and on Korean prose that word list fires on
grammar rather than on overreach. Treat the output as a list to skim, not a
list to fix — and consider narrowing the word list per book if you want it to
carry a signal.

### What was not run

`audit-book` needs a configured mutator/evaluator, so it was not part of this
sweep. The findings above are all from checks that run without a model.

## After the fixes

All eleven artifacts pass. Browsers confirm the mobile rule resolves to `100%`
rather than merely being present in the file, and all fifteen figures render in
the rebuilt EPUB.

The guard is worth more than the fix: the project's EPUB validator now fails on
leftover `srcset`, and that was verified by deliberately disabling the strip and
watching it name all fifteen documents. A check nobody has seen fail is not yet
known to work.
