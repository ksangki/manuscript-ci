from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StaticFinding:
    kind: str
    path: str
    detail: str


def apply_exact_once(text: str, find: str, replace: str) -> str:
    if not find:
        raise ValueError("empty FIND is not allowed")
    count = text.count(find)
    if count != 1:
        raise ValueError(f"FIND must occur exactly once; found {count}")
    return text.replace(find, replace, 1)


def paragraphs(text: str, minimum: int = 80) -> list[str]:
    chunks = re.split(r"\n\s*\n", text)
    return [c.strip() for c in chunks if len(c.strip()) >= minimum]


def normalize_paragraph(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def static_check(paths: list[Path]) -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    seen: dict[str, list[tuple[Path, str]]] = defaultdict(list)
    strong_terms = re.compile(
        r"(반드시|항상|절대로|유일(?:하|한|하게)?|모두|전부|대부분|예외 없이|틀림없이|무조건|자연히|저절로)"
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 200:
            findings.append(
                StaticFinding("short-file", str(path), "file is unusually short")
            )
        local: set[str] = set()
        for para in paragraphs(text):
            norm = normalize_paragraph(para)
            if norm in local:
                findings.append(
                    StaticFinding(
                        "duplicate-within-file",
                        str(path),
                        para[:160].replace("\n", " "),
                    )
                )
            local.add(norm)
            seen[norm].append((path, para))
        for match in strong_terms.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                StaticFinding(
                    "strong-claim-word",
                    str(path),
                    f"line {line}: {match.group(0)}",
                )
            )

    for entries in seen.values():
        distinct_paths = {str(path) for path, _ in entries}
        if len(distinct_paths) > 1:
            sample = entries[0][1][:160].replace("\n", " ")
            findings.append(
                StaticFinding(
                    "duplicate-across-files",
                    ", ".join(sorted(distinct_paths)),
                    sample,
                )
            )
    return findings
