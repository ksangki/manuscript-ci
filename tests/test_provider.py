import sys

from manuscript_ci.provider import CommandProvider


def test_command_provider_parses_json(tmp_path):
    script = tmp_path / "wrapper.py"
    script.write_text(
        "import json; print(json.dumps({'score': 91}))",
        encoding="utf-8",
    )
    provider = CommandProvider([sys.executable, str(script)], timeout_seconds=5)
    assert provider.call("hello")["score"] == 91
