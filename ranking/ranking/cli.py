"""CLI: validate input JSON, rank startups, write Markdown report.

Usage:
    python -m ranking inputs/startups.json out/report.md
    python -m ranking inputs/startups.json -          # write to stdout
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ranking.contract import StartupBatch
from ranking.report import render
from ranking.scoring import rank


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ranking",
        description="Deterministic ranking pipeline for pre-seed/seed tech startups.",
    )
    parser.add_argument("input", type=Path, help="Path to startups input JSON file.")
    parser.add_argument(
        "output",
        type=str,
        help="Path to write the Markdown report, or '-' for stdout.",
    )
    return parser.parse_args(argv)


def _load_batch(path: Path) -> StartupBatch:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return StartupBatch.model_validate(raw)


def run(input_path: Path, output: str) -> int:
    try:
        batch = _load_batch(input_path)
    except FileNotFoundError:
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON in {input_path}: {e}", file=sys.stderr)
        return 2
    except ValidationError as e:
        print(f"error: input failed contract validation:\n{e}", file=sys.stderr)
        return 2

    scored = rank(batch)
    md = render(scored)

    if output == "-":
        sys.stdout.write(md)
    else:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return run(args.input, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
