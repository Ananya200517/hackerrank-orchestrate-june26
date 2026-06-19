#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from pipeline.config import (  # noqa: E402
    DEFAULT_CLAIMS_PATH,
    DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_USER_HISTORY_PATH,
    REPO_ROOT,
)
from pipeline.output_writer import write_output_csv  # noqa: E402
from pipeline.processor import ClaimProcessor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the multi-modal evidence review pipeline on claims.csv."
    )
    parser.add_argument(
        "--claims",
        type=Path,
        default=DEFAULT_CLAIMS_PATH,
        help="Path to input claims CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to write output.csv.",
    )
    parser.add_argument(
        "--user-history",
        type=Path,
        default=DEFAULT_USER_HISTORY_PATH,
        help="Path to user_history.csv.",
    )
    parser.add_argument(
        "--evidence-requirements",
        type=Path,
        default=DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
        help="Path to evidence_requirements.csv.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve image paths.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    processor = ClaimProcessor(
        user_history_path=args.user_history,
        evidence_requirements_path=args.evidence_requirements,
        repo_root=args.repo_root,
    )
    outputs = processor.process_claims_csv(args.claims)
    write_output_csv(outputs, args.output)
    print(f"Processed {len(outputs)} claims -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
