from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import init_project, load_config
from .prompts import mutate_prompt, pairwise_prompt, score_prompt
from .provider import ProviderError
from .review import Reviewer
from .textops import static_check


def _paths(values: list[str]) -> list[Path]:
    result = [Path(v).resolve() for v in values]
    missing = [str(p) for p in result if not p.is_file()]
    if missing:
        raise FileNotFoundError("missing files: " + ", ".join(missing))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manuscript-ci",
        description="Conservative AI review for long-form manuscripts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create project templates")
    init.add_argument("directory", nargs="?", default=".")

    check = sub.add_parser("check", help="run static checks without an LLM")
    check.add_argument("files", nargs="+")

    review = sub.add_parser("review", help="review one manuscript file")
    review.add_argument("file")
    review.add_argument("--apply", action="store_true")
    review.add_argument("--max-iterations", type=int)
    review.add_argument("--candidates", type=int)

    audit = sub.add_parser("audit-book", help="cross-chapter semantic audit")
    audit.add_argument("files", nargs="+")

    prompt = sub.add_parser("prompt", help="print a raw review prompt")
    prompt.add_argument("file")
    prompt.add_argument("--kind", choices=["score", "mutate", "pairwise"], required=True)
    prompt.add_argument("--other", help="second file for pairwise mode")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            created = init_project(Path(args.directory))
            if not created:
                print("No files created; project files already exist.")
            else:
                for path in created:
                    print(f"created {path}")
            return 0

        if args.command == "check":
            findings = static_check(_paths(args.files))
            if not findings:
                print("No static findings.")
                return 0
            for item in findings:
                print(f"[{item.kind}] {item.path}: {item.detail}")
            return 0

        config = load_config(Path.cwd())
        reviewer = Reviewer(config)

        if args.command == "review":
            path = _paths([args.file])[0]
            report = reviewer.review_file(
                path,
                apply=args.apply,
                max_iterations=args.max_iterations,
                candidates=args.candidates,
            )
            print(f"Baseline: {report['baseline']['score']}")
            for iteration in report["iterations"]:
                kept = iteration["kept"]
                if kept:
                    print(
                        f"Iteration {iteration['number']}: KEEP → {iteration['ending_score']} | "
                        f"{kept['mutation']['reason']}"
                    )
                else:
                    print(f"Iteration {iteration['number']}: DISCARD all")
            print(f"Final: {report['final_score']}")
            print(f"Applied: {'yes' if report['applied'] else 'no'}")
            return 0

        if args.command == "audit-book":
            data = reviewer.audit_book(_paths(args.files))
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0

        if args.command == "prompt":
            path = _paths([args.file])[0]
            text = path.read_text(encoding="utf-8")
            if args.kind == "score":
                print(score_prompt(text, reviewer.brief, reviewer.dedup, reviewer.rubric))
            elif args.kind == "mutate":
                print(
                    mutate_prompt(
                        text,
                        reviewer.brief,
                        reviewer.dedup,
                        reviewer.rubric,
                        config.candidates,
                        0,
                    )
                )
            else:
                if not args.other:
                    raise ValueError("--other is required for pairwise mode")
                other = _paths([args.other])[0].read_text(encoding="utf-8")
                print(pairwise_prompt(text, other, reviewer.brief, reviewer.dedup, reviewer.rubric))
            return 0

        return 2
    except (FileNotFoundError, ValueError, ProviderError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
