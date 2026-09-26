from __future__ import annotations

import re
from typing import Any

from .models import PairwiseResult
from .provider import ProviderError

HARD_GATE_THRESHOLD = 0.5
# Keeps each excerpt well under Jev's 32k-token state budget even for CJK text.
MAX_EXCERPT_CHARS = 6000

WINNER_INSTRUCTIONS = (
    "`A` and `B` are two versions of the same manuscript passage that differ only by a small edit. "
    "Judged only against the project rules in `rules`, which version is better? "
    "Either one may be the original, and the original is allowed to win. "
    "Do not prefer a version merely because it reads smoother or more polished."
)

WINNER_CRITERIA = {
    "A": "`A` follows the project rules better than `B`.",
    "B": "`B` follows the project rules better than `A`.",
    "TIE": "Neither version is clearly better under the project rules.",
}

HARD_GATE_INSTRUCTIONS = (
    "Does `{this}` contain a hard-gate violation that `{other}` does not? "
    "Hard gates are listed in `rules.review_rubric`; typical ones are inventing a fact, citation, "
    "number, experience, or quote, making a claim stronger than the evidence, breaking a defined "
    "term or cross-chapter rule, materially weakening the author's voice, or changing meaning "
    "solely for stylistic smoothness."
)


def excerpt_bounds(a: str, b: str, context: int = 1, max_chars: int = MAX_EXCERPT_CHARS) -> tuple[int, int]:
    """Return `(start, tail)`: how much of the shared head and tail to cut from both texts.

    Whole chapters overflow the model's state budget, and the review loop only
    ever compares a text against a single FIND/REPLACE edit of itself.
    """
    prefix = 0
    limit = min(len(a), len(b))
    while prefix < limit and a[prefix] == b[prefix]:
        prefix += 1
    suffix = 0
    while suffix < limit - prefix and a[-1 - suffix] == b[-1 - suffix]:
        suffix += 1

    # Paragraphs are separated by blank lines; manuscripts without any fall back
    # to single newlines. A run of blank lines counts as one separator.
    separator = r"\n[ \t]*\n\s*" if re.search(r"\n[ \t]*\n", a) else r"\n+"
    change_end = len(a) - suffix
    before = [m.end() for m in re.finditer(separator, a) if m.end() <= prefix]
    after = [m.start() for m in re.finditer(separator, a) if m.start() >= change_end]

    # Both bounds stay inside the shared prefix/suffix, so the same offsets cut
    # `a` and `b` at the same place.
    start = before[-(context + 1)] if len(before) > context else 0
    end = after[context] if len(after) > context else len(a)
    if end - start > max_chars:
        margin = max(0, (max_chars - (change_end - prefix)) // 2)
        start = max(start, prefix - margin)
        end = min(end, change_end + margin)
    return start, len(a) - end


def changed_excerpts(a: str, b: str, context: int = 1, max_chars: int = MAX_EXCERPT_CHARS) -> tuple[str, str]:
    """Return the paragraphs where `a` and `b` differ, plus `context` paragraphs on each side."""
    if a == b:
        return "", ""
    start, tail = excerpt_bounds(a, b, context, max_chars)
    return a[start : len(a) - tail].strip(), b[start : len(b) - tail].strip()


class TypeSafePairwise:
    """Pairwise judge backed by a TypeSafe System One model instead of a command wrapper."""

    def __init__(
        self,
        brief: str,
        dedup: str,
        rubric: str,
        model: str,
        client: Any = None,
        min_probability: float = 0.6,
    ) -> None:
        self.rules = {
            key: value
            for key, value in {
                "writing_brief": brief,
                "dedup_decisions": dedup,
                "review_rubric": rubric,
            }.items()
            if value.strip()
        }
        self.model = model
        self.min_probability = min_probability
        self._client = client

    @staticmethod
    def _sdk() -> Any:
        try:
            import typesafe_sdk
        except ImportError as exc:
            raise ProviderError(
                "pairwise_backend = \"typesafe\" needs the SDK: pip install 'manuscript-ci[typesafe]'"
            ) from exc
        return typesafe_sdk

    def pairwise(self, a: str, b: str) -> PairwiseResult:
        if a == b:
            return PairwiseResult("TIE", reason="texts are identical")
        excerpt_a, excerpt_b = changed_excerpts(a, b)
        if excerpt_a == excerpt_b:
            return PairwiseResult("TIE", reason="edit only changes surrounding whitespace")

        sdk = self._sdk()
        Choice, Noul, TypeSafeError = sdk.Choice, sdk.Noul, sdk.TypeSafeError
        if self._client is None:
            self._client = sdk.TypeSafeClient(model=self.model)

        try:
            response = self._client.system_one(
                state={"rules": self.rules, "A": excerpt_a, "B": excerpt_b},
                questions={
                    "winner": Choice(instructions=WINNER_INSTRUCTIONS, criteria=WINNER_CRITERIA),
                    "hard_gate_a": Noul(instructions=HARD_GATE_INSTRUCTIONS.format(this="A", other="B")),
                    "hard_gate_b": Noul(instructions=HARD_GATE_INSTRUCTIONS.format(this="B", other="A")),
                },
            )
        except TypeSafeError as exc:
            raise ProviderError(f"TypeSafe pairwise call failed: {exc}") from exc

        winner_answer = response.choices["winner"]
        gate = {
            "A": response.nouls["hard_gate_a"].noul,
            "B": response.nouls["hard_gate_b"].noul,
        }
        winner = winner_answer.choice
        # A near-even split is not a win: the original is the incumbent.
        if winner != "TIE" and winner_answer.probabilities.get(winner, 0.0) < self.min_probability:
            winner = "TIE"
        if winner in gate:
            hard_gate = gate[winner] >= HARD_GATE_THRESHOLD
        else:
            hard_gate = max(gate.values()) >= HARD_GATE_THRESHOLD
        probs = ", ".join(
            f"P({option})={winner_answer.probabilities.get(option, 0.0):.2f}"
            for option in WINNER_CRITERIA
        )
        return PairwiseResult(
            winner,
            reason=(
                f"typesafe {response.model}: {probs}; "
                f"hard_gate A={gate['A']:.2f} B={gate['B']:.2f}"
            ),
            hard_gate=hard_gate,
        )
