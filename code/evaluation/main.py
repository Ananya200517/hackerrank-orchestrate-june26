#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from pipeline.config import (  # noqa: E402
    DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
    DEFAULT_SAMPLE_CLAIMS_PATH,
    DEFAULT_USER_HISTORY_PATH,
    OUTPUT_COLUMNS,
    REPO_ROOT,
)
from pipeline.data_loader import load_claims_csv  # noqa: E402
from pipeline.processor import ClaimProcessor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the pipeline against sample_claims.csv."
    )
    parser.add_argument(
        "--sample-claims",
        type=Path,
        default=DEFAULT_SAMPLE_CLAIMS_PATH,
        help="Path to labeled sample claims CSV.",
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


def load_expected_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compare_field(field: str, expected: str, predicted: str) -> bool:
    if field in {"evidence_standard_met", "valid_image"}:
        return expected.lower() == predicted.lower()
    return expected == predicted


def evaluate(
    expected_rows: list[dict[str, str]],
    predicted_rows: list[dict[str, str]],
) -> dict[str, object]:
    if len(expected_rows) != len(predicted_rows):
        raise ValueError(
            f"Row count mismatch: expected {len(expected_rows)}, got {len(predicted_rows)}"
        )

    scoreable_fields = [
        column
        for column in OUTPUT_COLUMNS
        if column not in {"user_id", "image_paths", "user_claim", "claim_object"}
    ]
    field_correct: Counter[str] = Counter()
    exact_match_rows = 0

    for expected, predicted in zip(expected_rows, predicted_rows, strict=True):
        row_exact = True
        for field in scoreable_fields:
            if compare_field(field, expected[field], predicted[field]):
                field_correct[field] += 1
            else:
                row_exact = False
        if row_exact:
            exact_match_rows += 1

    total = len(expected_rows)
    return {
        "total_rows": total,
        "exact_match_rows": exact_match_rows,
        "exact_match_rate": exact_match_rows / total if total else 0.0,
        "field_accuracy": {
            field: field_correct[field] / total if total else 0.0
            for field in scoreable_fields
        },
    }


def main() -> int:
    args = parse_args()
    processor = ClaimProcessor(
        user_history_path=args.user_history,
        evidence_requirements_path=args.evidence_requirements,
        repo_root=args.repo_root,
    )

    sample_claims = load_claims_csv(args.sample_claims, repo_root=args.repo_root)
    predicted = processor.process_claims(sample_claims)
    predicted_rows = [output.to_row() for output in predicted]
    expected_rows = load_expected_rows(args.sample_claims)

    metrics = evaluate(expected_rows, predicted_rows)

    print("Evaluation summary (skeleton baseline)")
    print(f"Rows evaluated: {metrics['total_rows']}")
    print(f"Exact row matches: {metrics['exact_match_rows']}")
    print(f"Exact row match rate: {metrics['exact_match_rate']:.2%}")
    print("Field accuracy:")
    for field, accuracy in metrics["field_accuracy"].items():
        print(f"  {field}: {accuracy:.2%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
