#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import asdict, dataclass
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
from pipeline.settings import load_settings  # noqa: E402
from pipeline.verifier import (  # noqa: E402
    DirectVLMClaimVerifier,
    StubClaimVerifier,
    VLMClaimVerifier,
)
from evaluation.main import SCOREABLE_FIELDS, compare_field, evaluate  # noqa: E402


@dataclass
class StrategyResult:
    name: str
    provider: str
    rows: int
    exact_match_rows: int
    exact_match_rate: float
    field_accuracy: dict[str, float]
    requests: int
    images_processed: int
    input_tokens: int
    output_tokens: int
    errors: int
    runtime_seconds: float


STRATEGIES = {
    "stub": lambda settings, provider: StubClaimVerifier(),
    "two_stage": lambda settings, provider: VLMClaimVerifier(settings=settings, provider=provider),
    "single_stage": lambda settings, provider: DirectVLMClaimVerifier(
        settings=settings, provider=provider
    ),
}


def load_expected_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_strategy(
    name: str,
    provider: str,
    sample_claims_path: Path,
    repo_root: Path,
    limit: int,
) -> StrategyResult:
    settings = load_settings(repo_root=repo_root)
    verifier = STRATEGIES[name](settings, provider)
    processor = ClaimProcessor(
        user_history_path=DEFAULT_USER_HISTORY_PATH,
        evidence_requirements_path=DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
        repo_root=repo_root,
        verifier=verifier,
    )

    claims = load_claims_csv(sample_claims_path, repo_root=repo_root)
    expected_rows = load_expected_rows(sample_claims_path)
    if limit > 0:
        claims = claims[:limit]
        expected_rows = expected_rows[:limit]

    started = time.perf_counter()
    predicted = processor.process_claims(claims)
    runtime_seconds = time.perf_counter() - started

    predicted_rows = [output.to_row() for output in predicted]
    metrics = evaluate(expected_rows, predicted_rows)

    usage = getattr(verifier, "usage", None)
    return StrategyResult(
        name=name,
        provider=provider if name != "stub" else "none",
        rows=metrics["total_rows"],
        exact_match_rows=metrics["exact_match_rows"],
        exact_match_rate=metrics["exact_match_rate"],
        field_accuracy=metrics["field_accuracy"],
        requests=usage.requests if usage else 0,
        images_processed=usage.images_processed if usage else 0,
        input_tokens=usage.input_tokens if usage else 0,
        output_tokens=usage.output_tokens if usage else 0,
        errors=usage.errors if usage else 0,
        runtime_seconds=runtime_seconds,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare verification strategies on sample_claims.csv."
    )
    parser.add_argument(
        "--sample-claims",
        type=Path,
        default=DEFAULT_SAMPLE_CLAIMS_PATH,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "anthropic"),
        default="anthropic",
        help="Provider for VLM-backed strategies.",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        choices=tuple(STRATEGIES),
        default=("stub", "two_stage", "single_stage"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Evaluate only the first N rows (0 = all).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(__file__).resolve().parent / "strategy_comparison.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[StrategyResult] = []

    for name in args.strategies:
        print(f"Running strategy: {name} ({args.provider if name != 'stub' else 'n/a'})")
        result = run_strategy(
            name=name,
            provider=args.provider,
            sample_claims_path=args.sample_claims,
            repo_root=args.repo_root,
            limit=args.limit,
        )
        results.append(result)
        print(
            f"  exact_match={result.exact_match_rows}/{result.rows} "
            f"({result.exact_match_rate:.1%}), "
            f"claim_status={result.field_accuracy.get('claim_status', 0):.1%}, "
            f"runtime={result.runtime_seconds:.1f}s, "
            f"requests={result.requests}, "
            f"tokens={result.input_tokens}+{result.output_tokens}",
        )

    payload = {
        "sample_claims": str(args.sample_claims),
        "provider": args.provider,
        "results": [asdict(item) for item in results],
    }
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
