from __future__ import annotations

from pipeline.models import ClaimInput, EvidenceRequirement


def requirements_for_claim(
    claim: ClaimInput,
    requirements: list[EvidenceRequirement],
) -> tuple[EvidenceRequirement, ...]:
    matched: list[EvidenceRequirement] = []
    for requirement in requirements:
        if requirement.claim_object in {"all", claim.claim_object}:
            matched.append(requirement)
    return tuple(matched)
