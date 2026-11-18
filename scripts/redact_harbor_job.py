"""Remove the CI provider key from Harbor output before displaying or uploading it."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def redact(paths: list[Path], key: str) -> int:
    """Replace exact key bytes in files under the given paths."""
    if not key:
        raise ValueError("OPENAI_API_KEY is required to verify Harbor output")
    token = key.encode()
    changed = 0
    for root in paths:
        files = [root] if root.is_file() else root.rglob("*") if root.exists() else []
        for path in files:
            if not path.is_file():
                continue
            content = path.read_bytes()
            if token in content:
                path.write_bytes(content.replace(token, b"[REDACTED]"))
                changed += 1
    return changed


if __name__ == "__main__":
    count = redact([Path(value) for value in sys.argv[1:]], os.environ.get("OPENAI_API_KEY", ""))
    print(f"Redacted {count} Harbor file(s).")
