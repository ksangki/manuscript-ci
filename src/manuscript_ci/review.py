from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .models import CandidateDecision, IterationResult, Mutation, PairwiseResult, ScoreResult
from .prompts import audit_book_prompt, extract_chapter_prompt, mutate_prompt, pairwise_prompt, score_prompt
from .provider import CommandProvider
from .textops import apply_exact_once


class Reviewer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.mutator = CommandProvider(config.mutator_command, config.timeout_seconds)
        self.evaluator = CommandProvider(config.evaluator_command, config.timeout_seconds)
        self.brief = self._read_optional(config.writing_brief)
        self.dedup = self._read_optional(config.dedup_decisions)
        self.rubric = self._read_optional(config.rubric)

    @staticmethod
    def _read_optional(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def score(self, text: str) -> ScoreResult:
        data = self.evaluator.call(score_prompt(text, self.brief, self.dedup, self.rubric))
        return ScoreResult.from_dict(data)

    def mutations(self, text: str, score: int, candidates: int) -> list[Mutation]:
        data = self.mutator.call(
            mutate_prompt(text, self.brief, self.dedup, self.rubric, candidates, score)
        )
        return [Mutation.from_dict(x) for x in data.get("candidates", []) if isinstance(x, dict)]

    def pairwise(self, a: str, b: str) -> PairwiseResult:
        data = self.evaluator.call(
            pairwise_prompt(a, b, self.brief, self.dedup, self.rubric)
        )
        return PairwiseResult.from_dict(data)

    def review_file(
        self,
        path: Path,
        *,
        apply: bool = False,
        max_iterations: int | None = None,
        candidates: int | None = None,
    ) -> dict:
        original = path.read_text(encoding="utf-8")
        current = original
        baseline = self.score(current)
        current_score = baseline.score
        iterations: list[IterationResult] = []
        iteration_limit = max_iterations or self.config.max_iterations
        candidate_limit = candidates or self.config.candidates

        for number in range(1, iteration_limit + 1):
            if current_score >= self.config.target_score:
                break
            proposed = self.mutations(current, current_score, candidate_limit)
            if not proposed:
                break

            decisions: list[CandidateDecision] = []
            accepted: list[tuple[int, CandidateDecision, str]] = []
            for mutation in proposed:
                try:
                    candidate_text = apply_exact_once(current, mutation.find, mutation.replace)
                except ValueError as exc:
                    decisions.append(
                        CandidateDecision(mutation, False, reason=str(exc))
                    )
                    continue

                forward = self.pairwise(current, candidate_text)
                reverse = self.pairwise(candidate_text, current)
                wins_forward = forward.winner == "B" and not forward.hard_gate
                wins_reverse = reverse.winner == "A" and not reverse.hard_gate
                if not (wins_forward and wins_reverse):
                    decisions.append(
                        CandidateDecision(
                            mutation,
                            False,
                            forward=forward,
                            reverse=reverse,
                            reason="candidate did not win both pairwise orders",
                        )
                    )
                    continue

                scored = self.score(candidate_text)
                if scored.hard_gate or scored.score < current_score:
                    decisions.append(
                        CandidateDecision(
                            mutation,
                            False,
                            score=scored.score,
                            forward=forward,
                            reverse=reverse,
                            reason="numeric score regressed or hard gate triggered",
                        )
                    )
                    continue

                decision = CandidateDecision(
                    mutation,
                    True,
                    score=scored.score,
                    forward=forward,
                    reverse=reverse,
                    reason="candidate won both pairwise orders",
                )
                decisions.append(decision)
                accepted.append((scored.score, decision, candidate_text))

            if not accepted:
                iterations.append(
                    IterationResult(number, current_score, current_score, decisions, None)
                )
                break

            accepted.sort(key=lambda item: item[0], reverse=True)
            new_score, kept, new_text = accepted[0]
            iterations.append(
                IterationResult(number, current_score, new_score, decisions, kept)
            )
            current = new_text
            current_score = new_score

        if apply and current != original:
            path.write_text(current, encoding="utf-8")

        report = {
            "tool": "manuscript-ci",
            "version": "0.1.0",
            "path": str(path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "baseline": asdict(baseline),
            "final_score": current_score,
            "changed": current != original,
            "applied": bool(apply and current != original),
            "iterations": [it.to_dict() for it in iterations],
        }
        self.write_report(path, report)
        return report

    def write_report(self, path: Path, report: dict) -> Path:
        self.config.report_dir.mkdir(parents=True, exist_ok=True)
        safe = path.name.replace(" ", "_")
        output = self.config.report_dir / f"{safe}.review.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return output

    def audit_book(self, paths: list[Path]) -> dict:
        indexes = []
        for path in paths:
            text = path.read_text(encoding="utf-8")
            indexes.append(self.evaluator.call(extract_chapter_prompt(text, str(path))))
        data = self.evaluator.call(
            audit_book_prompt(
                json.dumps(indexes, ensure_ascii=False, indent=2),
                self.brief,
                self.dedup,
                self.rubric,
            )
        )
        self.config.report_dir.mkdir(parents=True, exist_ok=True)
        output = self.config.report_dir / "book-audit.json"
        output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data
