"""Launch the interactive media-downloader application from a checkout.

This keeps the beginner-friendly ``python main.py`` workflow working without
requiring the package to be installed first.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Start the application's interactive CLI."""
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from media_downloader.cli import app

    app()


if __name__ == "__main__":
    main()
