from pathlib import Path

from manuscript_ci.config import init_project, load_config
from manuscript_ci.prompts import pairwise_prompt, score_prompt
from manuscript_ci.review import Reviewer


def test_ledger_section_only_when_ledger_given():
    assert "# FACT LEDGER" not in score_prompt("text", "brief", "", "rubric")
    prompt = score_prompt("text", "brief", "", "rubric", "- Block 2026-01-18: 50명 ✅")
    assert "# FACT LEDGER" in prompt
    assert "Block 2026-01-18" in prompt
    assert "remain subject to review" in prompt


def test_pairwise_prompt_carries_ledger():
    assert "Block 2026-01-18" in pairwise_prompt("a", "b", "", "", "", "Block 2026-01-18")


def test_reviewer_reads_fact_ledger(tmp_path: Path):
    init_project(tmp_path)
    assert load_config(tmp_path).fact_ledger == tmp_path / "FACT_LEDGER.md"
    assert Reviewer(load_config(tmp_path)).ledger == ""
    (tmp_path / "FACT_LEDGER.md").write_text("- checked ✅", encoding="utf-8")
    assert Reviewer(load_config(tmp_path)).ledger == "- checked ✅"
