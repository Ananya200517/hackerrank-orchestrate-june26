from __future__ import annotations

from pathlib import Path

from pipeline.config import (
    DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
    DEFAULT_USER_HISTORY_PATH,
    REPO_ROOT,
)
from pipeline.data_loader import (
    load_claims_csv,
    load_evidence_requirements_csv,
    load_user_history_csv,
)
from pipeline.evidence import requirements_for_claim
from pipeline.models import ClaimContext, ClaimInput, ClaimOutput
from pipeline.user_history import lookup_user_history, merge_history_risk_flags
from pipeline.risk_flags import sort_risk_flags
from pipeline.verifier import StubClaimVerifier, VLMClaimVerifier


class ClaimProcessor:
    def __init__(
        self,
        user_history_path: Path = DEFAULT_USER_HISTORY_PATH,
        evidence_requirements_path: Path = DEFAULT_EVIDENCE_REQUIREMENTS_PATH,
        repo_root: Path = REPO_ROOT,
        verifier: ClaimVerifier | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.user_history_by_id = load_user_history_csv(user_history_path)
        self.evidence_requirements = load_evidence_requirements_csv(
            evidence_requirements_path
        )
        self.verifier = verifier or VLMClaimVerifier()

    def build_context(self, claim: ClaimInput) -> ClaimContext:
        return ClaimContext(
            claim=claim,
            user_history=lookup_user_history(claim.user_id, self.user_history_by_id),
            evidence_requirements=requirements_for_claim(
                claim, self.evidence_requirements
            ),
        )

    def process_claim(self, claim: ClaimInput) -> ClaimOutput:
        context = self.build_context(claim)
        output = self.verifier.verify(context)

        history_flags = merge_history_risk_flags([], context.user_history)
        if history_flags:
            existing = [] if output.risk_flags == "none" else output.risk_flags.split(";")
            output.risk_flags = sort_risk_flags(
                ";".join(merge_history_risk_flags(existing, context.user_history))
            )
        else:
            output.risk_flags = sort_risk_flags(output.risk_flags)

        return output

    def process_claims(self, claims: list[ClaimInput]) -> list[ClaimOutput]:
        return [self.process_claim(claim) for claim in claims]

    def process_claims_csv(self, claims_path: Path) -> list[ClaimOutput]:
        claims = load_claims_csv(claims_path, repo_root=self.repo_root)
        return self.process_claims(claims)
