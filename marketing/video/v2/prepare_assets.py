#!/usr/bin/env python3
"""Stage repository-owned visual assets for the Remotion renderer."""

from __future__ import annotations

import shutil
from pathlib import Path


V2_DIR = Path(__file__).resolve().parent
VIDEO_DIR = V2_DIR.parent
REPOSITORY_DIR = VIDEO_DIR.parent.parent
PUBLIC_DIR = V2_DIR / "public"


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    for name in ("statement.png", "discoveries.png", "advisor.png", "import.png"):
        shutil.copy2(VIDEO_DIR / "source" / name, PUBLIC_DIR / name)

    shutil.copy2(
        REPOSITORY_DIR / "assets" / "daybook-mark.svg",
        PUBLIC_DIR / "daybook-mark.svg",
    )

    print(f"Staged Daybook assets in {PUBLIC_DIR}")


if __name__ == "__main__":
    main()
