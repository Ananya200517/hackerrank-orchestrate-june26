from __future__ import annotations

import csv
from pathlib import Path

from pipeline.config import REPO_ROOT
from pipeline.models import ClaimInput, EvidenceRequirement, ImageReference, UserHistory


def resolve_image_path(path: str, repo_root: Path = REPO_ROOT) -> Path:
    direct = (repo_root / path).resolve()
    if direct.exists():
        return direct

    dataset_path = (repo_root / "dataset" / path).resolve()
    if dataset_path.exists():
        return dataset_path

    return dataset_path


def parse_image_paths(image_paths: str, repo_root: Path = REPO_ROOT) -> tuple[ImageReference, ...]:
    references: list[ImageReference] = []
    for raw_path in image_paths.split(";"):
        path = raw_path.strip()
        if not path:
            continue
        absolute_path = resolve_image_path(path, repo_root=repo_root)
        image_id = Path(path).stem
        references.append(
            ImageReference(path=path, image_id=image_id, absolute_path=absolute_path)
        )
    return tuple(references)


def load_claims_csv(path: Path, repo_root: Path = REPO_ROOT) -> list[ClaimInput]:
    claims: list[ClaimInput] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            claims.append(
                ClaimInput(
                    user_id=row["user_id"],
                    image_paths=row["image_paths"],
                    user_claim=row["user_claim"],
                    claim_object=row["claim_object"],
                    images=parse_image_paths(row["image_paths"], repo_root=repo_root),
                )
            )
    return claims


def load_user_history_csv(path: Path) -> dict[str, UserHistory]:
    history_by_user: dict[str, UserHistory] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            history_by_user[row["user_id"]] = UserHistory(
                user_id=row["user_id"],
                past_claim_count=int(row["past_claim_count"]),
                accept_claim=int(row["accept_claim"]),
                manual_review_claim=int(row["manual_review_claim"]),
                rejected_claim=int(row["rejected_claim"]),
                last_90_days_claim_count=int(row["last_90_days_claim_count"]),
                history_flags=row["history_flags"],
                history_summary=row["history_summary"],
            )
    return history_by_user


def load_evidence_requirements_csv(path: Path) -> list[EvidenceRequirement]:
    requirements: list[EvidenceRequirement] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            requirements.append(
                EvidenceRequirement(
                    requirement_id=row["requirement_id"],
                    claim_object=row["claim_object"],
                    applies_to=row["applies_to"],
                    minimum_image_evidence=row["minimum_image_evidence"],
                )
            )
    return requirements
