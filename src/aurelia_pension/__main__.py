"""Command-line validation, build and local report server."""

import argparse
import functools
import http.server
import json
from pathlib import Path

from .data import load
from .pipeline import build


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Aurelia Pension BES analytics")
    parser.add_argument("command", choices=["validate", "build", "serve"], nargs="?", default="build")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--data-dir", type=Path, help="CSV input directory (never modified)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--json", action="store_true", help="Machine-readable validation summary")
    args = parser.parse_args(argv)
    if args.json and args.command != "validate":
        parser.error("--json is supported only with validate")
    if args.command == "serve" and not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    root = args.root.resolve()
    try:
        if args.command == "validate":
            directory = args.data_dir or root / "data/demo"
            funds, prices, _, checks = load(directory)
            summary = {"status": "PASS", "data_class": funds.data_class.iloc[0],
                       "fund_count": len(funds), "nav_dates": len(prices),
                       "price_observations": prices.size,
                       "start": prices.index[0].strftime("%Y-%m-%d"),
                       "end": prices.index[-1].strftime("%Y-%m-%d"),
                       "checks_passed": len(checks), "checks": checks}
            if args.json:
                print(json.dumps(summary, ensure_ascii=False))
            else:
                print(f"PASS: {summary['fund_count']} funds / {summary['price_observations']} "
                      f"NAV records / {summary['checks_passed']} controls. "
                      f"Data: {summary['data_class']}")
        elif args.command == "build":
            m = build(root, args.data_dir)
            print(f"Built {m['fund_count']} funds / {m['price_observations']} NAV records / "
                  f"{m['checks_passed']} controls. Data: {m['data_class']}")
            print(root / "artifacts/Aurelia_Pension_BES_Dashboard.html")
        else:
            # Explicit input must replace a stale report before the server starts.
            if args.data_dir is not None or not (root / "artifacts/Aurelia_Pension_BES_Dashboard.html").exists():
                build(root, args.data_dir)
            handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                        directory=str(root / "artifacts"))
            with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
                print(f"http://127.0.0.1:{args.port}/Aurelia_Pension_BES_Dashboard.html", flush=True)
                server.serve_forever()
    except (ValueError, OSError) as exc:
        if args.json:
            print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
            raise SystemExit(2) from None
        parser.error(str(exc))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
