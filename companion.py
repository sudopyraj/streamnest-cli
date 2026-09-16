"""Start the local StreamNest companion service.

The service listens only on localhost by default so downloads happen from the
user's own network connection rather than a hosted server.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from media_downloader.web import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local StreamNest companion.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: localhost)")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
