#!/usr/bin/env python3
"""
Quick helper to generate a QR_SECRET and persist it inside .env.

Usage: python scripts/generate_qr_secret.py
You can also run this script via a shell alias (e.g. `python -m scripts.generate_qr_secret`)
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path


def main() -> None:
    target = Path(".env")
    secret = secrets.token_urlsafe(28)
    entry = f"QR_SECRET={secret}"
    if target.exists():
        lines = target.read_text(encoding="utf-8").splitlines()
        updated = False
        for idx, line in enumerate(lines):
            if line.startswith("QR_SECRET="):
                lines[idx] = entry
                updated = True
                break
        if not updated:
            lines.append(entry)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        action = "updated" if updated else "added"
    else:
        target.write_text(entry + "\n", encoding="utf-8")
        action = "created"
    print(f"QR secret {action} in {target.resolve()}")


if __name__ == "__main__":
    sys.exit(main())
