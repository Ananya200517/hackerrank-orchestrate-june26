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
from pipeline.data_loader import load_claims_csv  # noqa: E402
from pipeline.output_writer import write_output_csv  # noqa: E402
from pipeline.processor import ClaimProcessor  # noqa: E402
from pipeline.settings import load_settings  # noqa: E402
from pipeline.verifier import StubClaimVerifier, VLMClaimVerifier  # noqa: E402


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
    parser.add_argument(
        "--provider",
        choices=("openai", "anthropic"),
        help="VLM provider override (defaults to DEFAULT_PROVIDER from .env).",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use the deterministic stub verifier instead of VLM calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process only the first N claims (0 = all).",
    )
    return parser.parse_args()


def build_verifier(args: argparse.Namespace):
    if args.stub:
        return StubClaimVerifier()
    settings = load_settings(repo_root=args.repo_root)
    return VLMClaimVerifier(settings=settings, provider=args.provider)


def main() -> int:
    args = parse_args()
    verifier = build_verifier(args)
    processor = ClaimProcessor(
        user_history_path=args.user_history,
        evidence_requirements_path=args.evidence_requirements,
        repo_root=args.repo_root,
        verifier=verifier,
    )

    claims = load_claims_csv(args.claims, repo_root=args.repo_root)
    if args.limit > 0:
        claims = claims[: args.limit]

    outputs = processor.process_claims(claims)
    write_output_csv(outputs, args.output)
    print(f"Processed {len(outputs)} claims -> {args.output}")

    if hasattr(verifier, "usage"):
        usage = verifier.usage
        print(
            "VLM usage:",
            f"requests={usage.requests}",
            f"images={usage.images_processed}",
            f"input_tokens={usage.input_tokens}",
            f"output_tokens={usage.output_tokens}",
            f"errors={usage.errors}",
        )
    return 0
