from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ImageReference:
    path: str
    image_id: str
    absolute_path: Path


@dataclass(frozen=True)
class ClaimInput:
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    images: tuple[ImageReference, ...] = field(default_factory=tuple)

    @property
    def image_ids(self) -> list[str]:
        return [image.image_id for image in self.images]


@dataclass(frozen=True)
class UserHistory:
    user_id: str
    past_claim_count: int
    accept_claim: int
    manual_review_claim: int
    rejected_claim: int
    last_90_days_claim_count: int
    history_flags: str
    history_summary: str

    @property
    def risk_flag_tokens(self) -> list[str]:
        if not self.history_flags or self.history_flags.strip().lower() == "none":
            return []
        return [flag.strip() for flag in self.history_flags.split(";") if flag.strip()]


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_id: str
    claim_object: str
    applies_to: str
    minimum_image_evidence: str


@dataclass(frozen=True)
class ClaimContext:
    claim: ClaimInput
    user_history: UserHistory | None
    evidence_requirements: tuple[EvidenceRequirement, ...]


@dataclass
class ClaimOutput:
    user_id: str
    image_paths: str
    user_claim: str
    claim_object: str
    evidence_standard_met: bool
    evidence_standard_met_reason: str
    risk_flags: str
    issue_type: str
    object_part: str
    claim_status: str
    claim_status_justification: str
    supporting_image_ids: str
    valid_image: bool
    severity: str

    def to_row(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "image_paths": self.image_paths,
            "user_claim": self.user_claim,
            "claim_object": self.claim_object,
            "evidence_standard_met": str(self.evidence_standard_met).lower(),
            "evidence_standard_met_reason": self.evidence_standard_met_reason,
            "risk_flags": self.risk_flags,
            "issue_type": self.issue_type,
            "object_part": self.object_part,
            "claim_status": self.claim_status,
            "claim_status_justification": self.claim_status_justification,
            "supporting_image_ids": self.supporting_image_ids,
            "valid_image": str(self.valid_image).lower(),
            "severity": self.severity,
        }
