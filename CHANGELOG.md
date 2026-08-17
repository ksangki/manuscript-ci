# Changelog

## Unreleased

- `check-build`: static checks on the built EPUB and HTML, for defects the prose
  review cannot see — leftover `srcset`/`sizes` on EPUB images, image sources
  missing from the archive, rounded rects distorted by
  `preserveAspectRatio="none"`, and pages with no `text-size-adjust` or viewport
  meta. Exits non-zero on findings so a release pipeline stops.
- `SKILL.md` / `SKILL_KO.md`: a built-artifact pass, including the pandoc
  table-column behaviour that has no automated check yet.
- `examples/github-actions/build-check.yml`: a workflow that gates published
  artifacts, with manual dispatch so an existing book can be checked without
  waiting for a change.
- `examples/FINDINGS.md`: measured results from nine published books.

## 0.1.0 — 2026-08-15

- Initial independent implementation.
- Conservative chapter review loop with exact FIND/REPLACE mutations.
- Numeric scoring and two-order pairwise gate.
- Original-wins-ties policy and hard gates.
- Whole-book semantic audit.
- Static duplicate and strong-claim checks.
- Agent `SKILL.md`.
- Korean practical guide and book-project templates.
- GitHub Actions example.
