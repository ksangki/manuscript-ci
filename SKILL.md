---
name: manuscript-ci-review
description: Review long-form book manuscripts conservatively. Preserve author voice, detect evidence overreach and cross-chapter inconsistency, propose surgical edits, and keep only changes that beat the original in pairwise evaluation.
---

# Manuscript CI Review Skill

Use this skill when the user asks to review, proofread, improve, edit, or quality-check a book manuscript or multiple chapters and wants the author's voice preserved.

## Core principle

The original manuscript is the incumbent. Do not rewrite merely because a sentence can be made smoother. Make a change only when a specific defect can be named and the edited version is demonstrably better under the project rubric.

## Required context order

Before changing manuscript text, read these files when present:

1. `WRITING_BRIEF.md`
2. `DEDUP_DECISIONS.md`
3. `REVIEW_RUBRIC.md`
4. the target chapter
5. adjacent chapters or the integrated manuscript when cross-chapter context is needed

If the project does not have these files, create working assumptions conservatively and clearly distinguish them from author-provided rules.

## Review targets

Prioritize:

- claims stronger than their evidence;
- invented causal inference from correlation or distribution;
- statistics interpreted beyond the source scope;
- contradictions between chapters;
- definition or terminology drift;
- cadence/date/number inconsistencies;
- repeated arguments that violate chapter ownership;
- invented personal experience or unsupported anecdotes;
- meta narration and generic AI prose;
- edits that flatten distinctive author voice;
- absolute language such as always, never, only, everyone, most, necessarily, unique, or inevitable when not supported.

Do not prioritize cosmetic rewriting when no defect exists.

## Mutation rule

Each candidate must be surgical and explainable in one sentence.

Prefer:

- one sentence replacement;
- one short paragraph deletion;
- one localized clarification;
- one terminology correction.

Avoid wholesale chapter rewrites.

Never create facts, citations, experiences, numbers, organizations, or events that are absent from the manuscript or verified sources.

## Pairwise gate

For every proposed edit:

1. Compare ORIGINAL as A vs CANDIDATE as B.
2. Judge only against the project rubric and hard gates.
3. Compare again with order reversed: CANDIDATE as A vs ORIGINAL as B.
4. KEEP only if the candidate wins both comparisons.
5. If either comparison is a tie or prefers the original, DISCARD.

The original wins uncertainty.

## Hard gates

Discard a candidate regardless of numeric score if it:

- fabricates or strengthens a factual claim without support;
- invents author experience;
- changes a defined term inconsistently;
- breaks a chapter-ownership decision;
- makes the author's voice materially more generic;
- removes necessary nuance from a contested or uncertain claim;
- changes meaning solely for stylistic smoothness.

## Whole-book audit

Before large-scale editing, inspect the entire manuscript for:

- repeated long passages;
- repeated claims with different wording;
- contradictory definitions;
- the same external statistic interpreted differently;
- conflicting schedules, dates, counts, thresholds, or stage definitions;
- concepts introduced as new after already being established;
- conclusions stated before the chapter that owns the argument.

Report cross-book issues first. Then edit only the chapters that actually need changes.

## Output style

For review reports, provide:

- issue location;
- why it matters;
- original wording;
- proposed wording;
- KEEP/DISCARD decision;
- short rationale.

When applying changes, summarize only material edits. Do not claim a whole-book numeric score unless the whole book was actually scored with the rubric.
