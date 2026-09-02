"""Build a deterministic weekly customer-feedback review from JSONL inputs.

See `templates/customer-feedback/README.md` for the intake contract this
script consumes and `scripts/customer_feedback_harness.py` for the module
that does the normalization and rendering.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from customer_feedback_harness import (  # noqa: E402
    FeedbackValidationError,
    build_weekly_review,
    load_feedback_jsonl,
)


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="JSONL files of summarized feedback records",
    )
    parser.add_argument(
        "--week-start",
        required=True,
        type=_date,
        help="Inclusive UTC date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--week-end",
        type=_date,
        help="Exclusive UTC date; defaults to seven days later",
    )
    parser.add_argument(
        "--pseudonym-namespace",
        default=None,
        help=(
            "Product-specific salt for reporter-reference pseudonymization "
            "(see the module docstring in customer_feedback_harness.py). "
            "Pick one per product and never change it."
        ),
    )
    parser.add_argument(
        "--extra-forbidden-fragment",
        action="append",
        default=[],
        dest="extra_forbidden_fragments",
        help=(
            "Additional key-name fragment this product's feedback must never "
            "contain (e.g. --extra-forbidden-fragment resume). Repeatable."
        ),
    )
    parser.add_argument(
        "--output", type=Path, help="Write Markdown here instead of stdout"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kwargs = {"extra_forbidden_fragments": args.extra_forbidden_fragments}
    if args.pseudonym_namespace:
        kwargs["pseudonym_namespace"] = args.pseudonym_namespace

    records = []
    rejected = []
    try:
        for path in args.inputs:
            result = load_feedback_jsonl(path, **kwargs)
            records.extend(result.records)
            rejected.extend(result.rejected)
        markdown = build_weekly_review(
            records, week_start=args.week_start, week_end=args.week_end, rejected=rejected
        )
    except (OSError, FeedbackValidationError) as exc:
        # A missing/unreadable file or an invalid week range is an operational
        # error and aborts the run; a malformed individual record does not —
        # it is collected in `rejected` and surfaced in the review instead.
        print(f"feedback review failed: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    if rejected:
        print(f"warning: {len(rejected)} record(s) rejected during load; see review output", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
