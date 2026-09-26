import random
import sys
from types import SimpleNamespace

import pytest

from manuscript_ci.provider import ProviderError
from manuscript_ci.typesafe_judge import TypeSafePairwise, changed_excerpts, excerpt_bounds


BEFORE = "첫 문단이다.\n\n둘째 문단은 반드시 옳다.\n\n셋째 문단이다.\n\n넷째 문단이다."
AFTER = BEFORE.replace("반드시 옳다", "대체로 옳다")


def test_excerpt_keeps_changed_paragraph_and_neighbors():
    a, b = changed_excerpts(BEFORE, AFTER)
    assert a == "첫 문단이다.\n\n둘째 문단은 반드시 옳다.\n\n셋째 문단이다."
    assert b == "첫 문단이다.\n\n둘째 문단은 대체로 옳다.\n\n셋째 문단이다."


def test_excerpt_without_context_is_only_the_changed_paragraph():
    assert changed_excerpts(BEFORE, AFTER, context=0) == (
        "둘째 문단은 반드시 옳다.",
        "둘째 문단은 대체로 옳다.",
    )


def test_excerpt_of_identical_texts_is_empty():
    assert changed_excerpts(BEFORE, BEFORE) == ("", "")


def test_excerpt_treats_a_run_of_blank_lines_as_one_break():
    a = "p0\n\np1\n\n\n\np2 old\n\n\n\np3\n\np4"
    assert changed_excerpts(a, a.replace("old", "new")) == (
        "p1\n\n\n\np2 old\n\n\n\np3",
        "p1\n\n\n\np2 new\n\n\n\np3",
    )


def test_excerpt_falls_back_to_single_newlines():
    a = "\n".join(f"line {i}" for i in range(1000)) + "\nold\n" + "\n".join("tail" for _ in range(1000))
    x, y = changed_excerpts(a, a.replace("old", "new"))
    assert x == "line 999\nold\ntail"
    assert y == "line 999\nnew\ntail"


def test_excerpt_is_capped_around_the_change():
    a = ("가" * 20000) + " old " + ("나" * 20000)
    x, y = changed_excerpts(a, a.replace("old", "new"), max_chars=1000)
    assert len(x) <= 1000 and "old" in x
    assert y == x.replace("old", "new")


def test_excerpts_stay_aligned_on_random_edits():
    rng = random.Random(0)
    for _ in range(3000):
        a = "".join(rng.choice("ab \n") for _ in range(rng.randint(1, 40)))
        i = rng.randint(0, len(a))
        j = rng.randint(i, len(a))
        b = a[:i] + "".join(rng.choice("ab\n") for _ in range(rng.randint(0, 5))) + a[j:]
        if a == b:
            continue
        start, tail = excerpt_bounds(a, b, rng.randint(0, 2), rng.choice([4, 10**6]))
        # Only text shared by both versions may be cut away.
        assert a[:start] == b[:start]
        assert a[len(a) - tail :] == b[len(b) - tail :]
        assert start <= len(a) - tail and start <= len(b) - tail


def test_missing_sdk_is_a_provider_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "typesafe_sdk", None)
    with pytest.raises(ProviderError, match="manuscript-ci\\[typesafe\\]"):
        TypeSafePairwise("", "", "", "jev-latest").pairwise(BEFORE, AFTER)


def test_whitespace_only_edit_is_a_tie_with_its_own_reason():
    result = TypeSafePairwise("", "", "", "jev-latest").pairwise("p1\n\np2", "p1\n\np2\n")
    assert result.winner == "TIE"
    assert "whitespace" in result.reason


class FakeClient:
    def __init__(self, winner, probabilities, gate_a, gate_b):
        self.response = SimpleNamespace(
            model="jev-test",
            choices={"winner": SimpleNamespace(choice=winner, probabilities=probabilities)},
            nouls={
                "hard_gate_a": SimpleNamespace(noul=gate_a),
                "hard_gate_b": SimpleNamespace(noul=gate_b),
            },
        )
        self.calls = []

    def system_one(self, state, questions):
        self.calls.append((state, questions))
        return self.response


def _judge(client):
    return TypeSafePairwise("brief", "", "rubric", "jev-latest", client=client)


def test_winner_and_probabilities_are_reported():
    pytest.importorskip("typesafe_sdk")
    client = FakeClient("B", {"A": 0.1, "B": 0.85, "TIE": 0.05}, 0.2, 0.1)
    result = _judge(client).pairwise(BEFORE, AFTER)
    assert result.winner == "B"
    assert result.hard_gate is False
    assert "P(B)=0.85" in result.reason
    state, questions = client.calls[0]
    assert state["rules"] == {"writing_brief": "brief", "review_rubric": "rubric"}
    assert "대체로" in state["B"] and "대체로" not in state["A"]
    assert set(questions) == {"winner", "hard_gate_a", "hard_gate_b"}


def test_hard_gate_follows_the_winner():
    pytest.importorskip("typesafe_sdk")
    # The loser's violation must not block the winner.
    client = FakeClient("B", {"A": 0.1, "B": 0.9, "TIE": 0.0}, 0.9, 0.1)
    assert _judge(client).pairwise(BEFORE, AFTER).hard_gate is False
    client = FakeClient("B", {"A": 0.1, "B": 0.9, "TIE": 0.0}, 0.1, 0.7)
    assert _judge(client).pairwise(BEFORE, AFTER).hard_gate is True


def test_identical_texts_skip_the_api():
    client = FakeClient("A", {}, 0.0, 0.0)
    result = _judge(client).pairwise(BEFORE, BEFORE)
    assert result.winner == "TIE"
    assert client.calls == []
