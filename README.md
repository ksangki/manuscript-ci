# Manuscript CI

**English** | [한국어](README_KO.md)

**AI review that protects the author's voice.**

Manuscript CI is an open-source review workflow for long-form writing. It does not try to rewrite a book into generic “AI-clean” prose. Instead it proposes small editorial changes, evaluates them against the author's rules, compares each candidate against the original in both orders, and keeps only verified improvements.

Think of it as **lint + tests + code review for manuscripts**.

> We don't write your book. We protect it while helping you revise it.

## Why this exists

Most AI writing tools are optimized to generate or rewrite. Books need a different failure model:

- a fact can become stronger than its source;
- a definition can drift between chapters;
- the same argument can quietly repeat five times;
- a local edit can flatten the author's voice;
- a revision can introduce a new contradiction elsewhere;
- a “better sounding” sentence can actually be less true.

Manuscript CI treats the **original as the incumbent**. A candidate edit must beat it to survive.

## Core loop

```text
manuscript
   ↓
small edit candidates
   ↓
rubric score
   ↓
pairwise compare: Original vs Candidate
   ↓
pairwise compare again with order reversed
   ↓
KEEP only if the candidate wins both
   ↓
report / optional apply
```

For a whole book, Manuscript CI also supports a cross-chapter audit for repeated claims, terminology drift, conflicting numbers, ownership conflicts, and cadence inconsistencies.

## 5-minute start

Requires Python 3.11+.

### Option A — use it as an AI agent skill

This is the fastest path if you already use Codex, Claude Code, Gemini CLI, or another coding agent with access to your manuscript repository. Copy `SKILL.md` into your agent skill setup, or simply ask the agent to follow the file in this repository. Then add the three project rules below to your book repo and request a Manuscript CI review.

A Korean explanation of the skill is available in [SKILL_KO.md](SKILL_KO.md).

### Option B — install the CLI

Install directly from GitHub:

```bash
python -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/ksangki/manuscript-ci.git"
manuscript-ci init .
```

For development, clone this repository and use `pip install -e .`.

This creates:

```text
manuscript-ci.toml
WRITING_BRIEF.md
DEDUP_DECISIONS.md
REVIEW_RUBRIC.md
```

Connect any LLM through two wrapper commands in `manuscript-ci.toml`:

```toml
[models]
mutator_command = ["./scripts/my-mutator"]
evaluator_command = ["./scripts/my-evaluator"]
timeout_seconds = 180
```

Each wrapper receives a prompt on **stdin** and must print JSON on **stdout**. This keeps the core tool provider-neutral: Claude, Codex, Gemini, Ollama, an internal LLM gateway, or any API can be used behind the wrapper.

Review one chapter:

```bash
manuscript-ci review chapters/04.md
```

Nothing is changed by default. To apply verified edits:

```bash
manuscript-ci review chapters/04.md --apply
```

Audit a whole book without rewriting it:

```bash
manuscript-ci audit-book chapters/*.md
```

Run static checks without any LLM:

```bash
manuscript-ci check chapters/*.md
```

## The three project files that matter most

### `WRITING_BRIEF.md`

Defines the author's voice and editorial constraints: audience, tone, terminology, claims policy, forbidden patterns, and what must be preserved.

### `DEDUP_DECISIONS.md`

Defines which chapter “owns” a concept. This prevents a book from rediscovering the same idea in every chapter.

### `REVIEW_RUBRIC.md`

Defines what “better” means. A useful rubric usually scores:

- factual discipline;
- argument consistency;
- cross-chapter consistency;
- author voice;
- repetition;
- reader usefulness;
- clarity without oversmoothing.

## Safety defaults

Manuscript CI is intentionally conservative.

- **No write by default.** `--apply` is required.
- **Exact replacements only.** A mutation is rejected unless its FIND text occurs exactly once.
- **Original wins ties.** If the evaluator is uncertain, the manuscript stays unchanged.
- **Order-bias check.** Pairwise comparison runs twice with A/B reversed.
- **Hard gates.** Fabricated facts, invented experience, source overclaiming, or author-voice damage can reject an edit even when the numeric score rises.
- **Small changes.** The mutator is asked for surgical edits, not chapter rewrites.

## Commands

```text
manuscript-ci init [DIR]
manuscript-ci check FILE [FILE ...]
manuscript-ci check-build FILE.epub|FILE.html [...]
manuscript-ci review FILE [--apply] [--max-iterations N]
manuscript-ci audit-book FILE [FILE ...]
manuscript-ci prompt FILE --kind mutate|score|pairwise
```

See [GUIDE_KO.md](GUIDE_KO.md) for a practical Korean guide.

## Checking what the reader actually opens

`check` and `review` read the manuscript. `check-build` reads what the manuscript
was turned into, because a book can pass every prose gate and still arrive broken:

- **`epub-responsive-img`** — an `<img>` in an EPUB still carrying `srcset`/`sizes`.
  Builders rewrite `src` to the path inside the archive and leave `srcset` pointing
  at the web tree. Reading systems prefer `srcset`, and HTML does not fall back to
  `src` when the candidate is missing, so every figure renders as a blank box while
  a perfectly valid `src` sits unused.
- **`epub-image-missing`** — an image `src` that is not in the archive at all.
- **`svg-stretched-corner`** — a rounded `<rect>` inside `preserveAspectRatio="none"`.
  The radius is in user units, so each axis scales it differently and the rounded cap
  renders as an ellipse. Bar charts are where this shows: the shortest bar becomes a
  lozenge. The wider the reading column, the worse it looks.
- **`html-no-text-size-adjust`** — a page that lets mobile browsers resize text per
  block. In a table wide enough to scroll sideways, the long column inflates and the
  short ones do not, so one table renders at two different font sizes.
- **`html-no-viewport`** — a page with no viewport meta.

Unlike `check`, this command exits non-zero when it finds something, so a release
pipeline stops on it. Every one of these defects shipped in a real book and was
found by a reader, not by a build that reported success.

## Using it as an AI agent skill

`SKILL.md` contains a model-agnostic skill definition. Copy the repository or the skill file into your agent environment and ask:

```text
이 책을 Manuscript CI 방식으로 검토해줘.
원문보다 확실히 나은 수정만 남기고, 저자 목소리는 보존해줘.
```

The skill directs the agent to read the project brief, dedup rules and rubric before editing, then use small mutations and pairwise decisions rather than wholesale rewriting.

## GitHub Actions

An example workflow is included at:

```text
examples/github-actions/manuscript-ci.yml
```

The recommended CI mode is **report-only**. Let CI comment on manuscript regressions; keep actual editorial writes explicit.

## Real-world origin

The workflow was generalized from a full-book review where a long-form manuscript was edited using small mutations, explicit quality criteria, pairwise decisions, cross-chapter consistency checks, and a final human pass. The important lesson was that the biggest wins did not come from “making prose prettier”; they came from catching unsupported causal claims, definition drift, duplicated ownership, inconsistent cadence, and edits that weakened the author's own voice.

## Acknowledgement

Manuscript CI was inspired by the mutate → evaluate → pairwise keep/revert loop in [`crimeacs/auto-improve`](https://github.com/crimeacs/auto-improve), which is MIT licensed. Manuscript CI is an independent implementation focused on long-form manuscripts and does not vendor the upstream source.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) or the [Korean contributing guide](CONTRIBUTING_KO.md).

## License

MIT. See [LICENSE](LICENSE).
