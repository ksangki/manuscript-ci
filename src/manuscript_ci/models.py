from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Mutation:
    find: str
    replace: str
    reason: str
    risk: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Mutation":
        return cls(
            find=str(data.get("find", "")),
            replace=str(data.get("replace", "")),
            reason=str(data.get("reason", "")),
            risk=str(data.get("risk", "")),
        )


@dataclass
class ScoreResult:
    score: int
    issues: list[str] = field(default_factory=list)
    hard_gate: bool = False
    rationale: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScoreResult":
        score = int(data.get("score", data.get("total_score", 0)))
        issues = [str(x) for x in data.get("issues", [])]
        return cls(
            score=max(0, min(100, score)),
            issues=issues,
            hard_gate=bool(data.get("hard_gate", False)),
            rationale=str(data.get("rationale", data.get("reason", ""))),
        )


@dataclass
class PairwiseResult:
    winner: str
    reason: str = ""
    hard_gate: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PairwiseResult":
        winner = str(data.get("winner", "TIE")).upper()
        if winner not in {"A", "B", "TIE"}:
            winner = "TIE"
        return cls(
            winner=winner,
            reason=str(data.get("reason", data.get("rationale", ""))),
            hard_gate=bool(data.get("hard_gate", False)),
        )


@dataclass
class CandidateDecision:
    mutation: Mutation
    accepted: bool
    score: int | None = None
    forward: PairwiseResult | None = None
    reverse: PairwiseResult | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutation": asdict(self.mutation),
            "accepted": self.accepted,
            "score": self.score,
            "forward": asdict(self.forward) if self.forward else None,
            "reverse": asdict(self.reverse) if self.reverse else None,
            "reason": self.reason,
        }


@dataclass
class IterationResult:
    number: int
    starting_score: int
    ending_score: int
    decisions: list[CandidateDecision]
    kept: CandidateDecision | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "starting_score": self.starting_score,
            "ending_score": self.ending_score,
            "decisions": [d.to_dict() for d in self.decisions],
            "kept": self.kept.to_dict() if self.kept else None,
        }
