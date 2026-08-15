from __future__ import annotations

import tomllib
from importlib.resources import files
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    root: Path
    max_iterations: int
    candidates: int
    target_score: int
    mutator_command: list[str]
    evaluator_command: list[str]
    timeout_seconds: int
    writing_brief: Path
    dedup_decisions: Path
    rubric: Path
    report_dir: Path


def load_config(start: Path | None = None) -> Config:
    root = (start or Path.cwd()).resolve()
    config_path = root / "manuscript-ci.toml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"{config_path} not found. Run `manuscript-ci init .` first."
        )
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    review = data.get("review", {})
    models = data.get("models", {})
    context = data.get("context", {})
    output = data.get("output", {})

    return Config(
        root=root,
        max_iterations=int(review.get("max_iterations", 4)),
        candidates=int(review.get("candidates", 3)),
        target_score=int(review.get("target_score", 92)),
        mutator_command=[str(x) for x in models.get("mutator_command", [])],
        evaluator_command=[str(x) for x in models.get("evaluator_command", [])],
        timeout_seconds=int(models.get("timeout_seconds", 180)),
        writing_brief=root / str(context.get("writing_brief", "WRITING_BRIEF.md")),
        dedup_decisions=root / str(context.get("dedup_decisions", "DEDUP_DECISIONS.md")),
        rubric=root / str(context.get("rubric", "REVIEW_RUBRIC.md")),
        report_dir=root / str(output.get("report_dir", ".manuscript-ci/reports")),
    )


def init_project(target: Path) -> list[Path]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    template_root = files("manuscript_ci").joinpath("_templates")
    mappings = {
        "manuscript-ci.toml": target / "manuscript-ci.toml",
        "WRITING_BRIEF.md": target / "WRITING_BRIEF.md",
        "DEDUP_DECISIONS.md": target / "DEDUP_DECISIONS.md",
        "REVIEW_RUBRIC.md": target / "REVIEW_RUBRIC.md",
    }
    created: list[Path] = []
    for name, destination in mappings.items():
        if destination.exists():
            continue
        source = template_root.joinpath(name)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        created.append(destination)
    return created
