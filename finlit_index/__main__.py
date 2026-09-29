"""Command-line entry point: python -m finlit_index."""

from __future__ import annotations

import argparse
from pathlib import Path
import logging

import requests

from .directory import fetch_directory, parse_directory, representative_sample, write_csv, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Index a public financial education directory")
    parser.add_argument("--output", type=Path, default=Path("output/resources.csv"))
    parser.add_argument("--report", type=Path, default=Path("output/report.html"))
    parser.add_argument("--sample-output", type=Path, help="Optional metadata-only sample CSV")
    parser.add_argument("--sample-size", type=int, default=12)
    parser.add_argument("--from-html", type=Path, help="Use a saved HTML page instead of fetching live")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    if args.sample_size < 1 or args.timeout <= 0:
        parser.error("--sample-size and --timeout must be positive")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        page_html = args.from_html.read_text(encoding="utf-8") if args.from_html else fetch_directory(args.timeout)
        resources = parse_directory(page_html)
        write_csv(resources, args.output)
        write_report(resources, args.report)
        if args.sample_output:
            write_csv(representative_sample(resources, args.sample_size), args.sample_output, sample=True)
    except (OSError, PermissionError, ValueError, requests.RequestException) as exc:
        logging.error("Indexing failed: %s", exc)
        return 1
    logging.info("Indexed %s entries across %s categories", len(resources), len({r.category for r in resources}))
    logging.info("Saved full local CSV to %s and report to %s", args.output, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
