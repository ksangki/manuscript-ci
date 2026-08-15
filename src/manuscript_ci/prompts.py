from __future__ import annotations


def _context(brief: str, dedup: str, rubric: str) -> str:
    return f"""# WRITING BRIEF\n{brief}\n\n# DEDUP DECISIONS\n{dedup}\n\n# REVIEW RUBRIC\n{rubric}\n"""


def score_prompt(text: str, brief: str, dedup: str, rubric: str) -> str:
    return f"""You are the evaluator for a long-form manuscript. Score the artifact conservatively against the rubric. Do not reward generic smoothness. Penalize unsupported claims, definition drift, repetition, and loss of author voice.\n\n{_context(brief, dedup, rubric)}\n\n# ARTIFACT\n{text}\n\nReturn JSON only:\n{{\"score\": 0, \"issues\": [\"...\"], \"hard_gate\": false, \"rationale\": \"...\"}}\n"""


def mutate_prompt(
    text: str,
    brief: str,
    dedup: str,
    rubric: str,
    candidates: int,
    current_score: int,
) -> str:
    return f"""You are a conservative book editor. The current manuscript already scored {current_score}/100. Find only visible defects. Do NOT rewrite for style alone. Propose at most {candidates} small, independent exact FIND/REPLACE edits. If the text is already good, return an empty candidate list.\n\nPriority defects: evidence overreach, causal inference not supported by the source, inconsistent definitions/numbers/cadence, duplicated ownership, generic AI prose, and sentences that weaken the author's own voice.\n\nEvery FIND must be copied verbatim from the artifact and should occur exactly once. Keep replacements surgical.\n\n{_context(brief, dedup, rubric)}\n\n# ARTIFACT\n{text}\n\nReturn JSON only:\n{{\"candidates\":[{{\"find\":\"exact text\",\"replace\":\"replacement\",\"reason\":\"specific defect fixed\",\"risk\":\"what could be lost\"}}]}}\n"""


def pairwise_prompt(
    a: str,
    b: str,
    brief: str,
    dedup: str,
    rubric: str,
) -> str:
    return f"""Compare manuscript A and B. Judge only against the project rules. The original is allowed to win. Do not prefer a version merely because it is smoother or more polished. A hard-gate violation overrides score.\n\n{_context(brief, dedup, rubric)}\n\n# A\n{a}\n\n# B\n{b}\n\nReturn JSON only:\n{{\"winner\":\"A|B|TIE\",\"hard_gate\":false,\"reason\":\"...\"}}\n"""


def extract_chapter_prompt(text: str, path: str) -> str:
    return f"""Extract a compact semantic index for one book chapter. Do not critique or rewrite. Identify the chapter's core claims, definitions, external numbers, named concepts it appears to own, recurring metaphors, schedules/cadences/thresholds, and explicit references to other chapters.\n\n# PATH\n{path}\n\n# CHAPTER\n{text}\n\nReturn JSON only:\n{{\"path\":\"{path}\",\"claims\":[],\"definitions\":{{}},\"numbers\":[],\"owned_concepts\":[],\"metaphors\":[],\"cadences\":[],\"cross_references\":[]}}\n"""


def audit_book_prompt(indexes_json: str, brief: str, dedup: str, rubric: str) -> str:
    return f"""Audit a whole-book semantic index. Do not rewrite the manuscript. Find only cross-chapter problems with meaningful editorial impact: contradictory definitions, the same statistic interpreted differently, conflicting dates/cadences/thresholds, repeated claims that violate ownership, concepts re-introduced as new after being established, and conclusions stated before the chapter that owns the argument.\n\n{_context(brief, dedup, rubric)}\n\n# CHAPTER INDEXES\n{indexes_json}\n\nReturn JSON only:\n{{\"issues\":[{{\"severity\":\"high|medium|low\",\"type\":\"...\",\"chapters\":[],\"detail\":\"...\",\"recommendation\":\"...\"}}],\"summary\":\"...\"}}\n"""
