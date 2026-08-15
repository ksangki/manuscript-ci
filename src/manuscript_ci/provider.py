from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    pass


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        data = json.loads(stripped)
        if not isinstance(data, dict):
            raise ValueError("top-level JSON must be an object")
        return data
    except Exception:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(stripped[start : end + 1])
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        raise ProviderError("LLM wrapper did not return a JSON object")


@dataclass
class CommandProvider:
    command: list[str]
    timeout_seconds: int = 180

    def call(self, prompt: str) -> dict[str, Any]:
        if not self.command:
            raise ProviderError("LLM command is not configured")
        try:
            result = subprocess.run(
                self.command,
                input=prompt,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ProviderError(f"command not found: {self.command[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                f"LLM wrapper timed out after {self.timeout_seconds}s: {shlex.join(self.command)}"
            ) from exc

        if result.returncode != 0:
            detail = result.stderr.strip()[-1000:]
            raise ProviderError(
                f"LLM wrapper failed ({result.returncode}): {shlex.join(self.command)}\n{detail}"
            )
        return _extract_json(result.stdout)
