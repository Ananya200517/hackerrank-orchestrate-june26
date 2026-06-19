from __future__ import annotations

from pathlib import Path

from pipeline.models import ClaimContext, ClaimOutput


class ClaimVerifier:
    """Placeholder verifier. Replace with VLM/LLM logic in a later iteration."""

    def verify(self, context: ClaimContext) -> ClaimOutput:
        claim = context.claim
        missing_images = [
            image.path for image in claim.images if not image.absolute_path.exists()
        ]

        if missing_images:
            return ClaimOutput(
                user_id=claim.user_id,
                image_paths=claim.image_paths,
                user_claim=claim.user_claim,
                claim_object=claim.claim_object,
                evidence_standard_met=False,
                evidence_standard_met_reason=(
                    "One or more referenced image files could not be loaded."
                ),
                risk_flags="damage_not_visible",
                issue_type="unknown",
                object_part="unknown",
                claim_status="not_enough_information",
                claim_status_justification=(
                    "The pipeline skeleton could not access all submitted images."
                ),
                supporting_image_ids="none",
                valid_image=False,
                severity="unknown",
            )

        return ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "Verification logic is not implemented yet; evidence review pending."
            ),
            risk_flags="none",
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification=(
                "Pipeline skeleton loaded the claim and images but has not run "
                "visual analysis yet."
            ),
            supporting_image_ids="none",
            valid_image=True,
            severity="unknown",
        )
