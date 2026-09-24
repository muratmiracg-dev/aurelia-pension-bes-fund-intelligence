"""Command-line build and local report server."""

import argparse
import functools
import http.server
from pathlib import Path

from .pipeline import build


def main() -> None:
    parser = argparse.ArgumentParser(description="Aurelia Pension BES analytics")
    parser.add_argument("command", choices=["build", "serve"], nargs="?", default="build")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--data-dir", type=Path, help="Validated external CSV directory")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "build":
        m = build(root, args.data_dir)
        print(f"Built {m['fund_count']} funds / {m['price_observations']} NAV records / "
              f"{m['checks_passed']} controls. Data: {m['data_class']}")
        print(root / "artifacts/Aurelia_Pension_BES_Dashboard.html")
    else:
        if not (root / "artifacts/Aurelia_Pension_BES_Dashboard.html").exists():
            build(root, args.data_dir)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                    directory=str(root / "artifacts"))
        with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"http://127.0.0.1:{args.port}/Aurelia_Pension_BES_Dashboard.html", flush=True)
            server.serve_forever()


if __name__ == "__main__":
    main()
