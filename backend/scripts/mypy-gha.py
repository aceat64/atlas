"""
Takes mypy json from stdin and converts to GitHub annotation output.

Example usage:
uv run mypy app --output json | uv run scripts/mypy-gha.py
"""

import json
import sys

for line in sys.stdin:
    error = json.loads(line)

    command = "error" if error["severity"] == "error" else "notice"
    title = f"Mypy ({error['code']})" if error["code"] is not None else "Mypy"

    message = f"{error['message']}."

    if error["hint"]:
        message += f"%0A%0A{error['hint']}"

    print(f"::{command} file={error['file']},line={error['line']},col={error['column']},title={title}::{message}")
