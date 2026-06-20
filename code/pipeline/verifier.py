from __future__ import annotations

import time

from pipeline.adjudicator import build_output
from pipeline.models import ClaimContext, ClaimOutput
from pipeline.perception import parse_perception_response
from pipeline.settings import Settings, load_settings
from pipeline.vlm_client import VLMClient, VLMUsageStats


class StubClaimVerifier:
    """Deterministic fallback when API calls are disabled."""

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
                    "The pipeline could not access all submitted images."
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
                "Stub verifier enabled; visual analysis was not run."
            ),
            risk_flags="none",
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification=(
                "Stub verifier is active. Enable the VLM verifier to analyze images."
            ),
            supporting_image_ids="none",
            valid_image=True,
            severity="unknown",
        )


class VLMClaimVerifier:
    """Human-like two-stage verifier: visual perception then service-desk adjudication."""

    def __init__(
        self,
        settings: Settings | None = None,
        provider: str | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.provider = provider or self.settings.default_provider
        self.client = VLMClient(settings=self.settings, provider=self.provider)
        self.usage = self.client.usage

    def verify(self, context: ClaimContext) -> ClaimOutput:
        claim = context.claim
        missing_images = [
            image.path for image in claim.images if not image.absolute_path.exists()
        ]
        if missing_images:
            return StubClaimVerifier().verify(context)

        perception: dict = {}
        attempts = self.settings.max_retries + 1

        for attempt in range(attempts):
            try:
                raw_response = self.client.analyze_perception(context)
                perception = parse_perception_response(raw_response)
                break
            except Exception:  # noqa: BLE001 - perception informs but is not required
                self.usage.errors += 1
                if attempt < attempts - 1:
                    time.sleep(1.5 * (attempt + 1))

        try:
            return build_output(context, perception)
        except Exception as exc:
            return ClaimOutput(
                user_id=claim.user_id,
                image_paths=claim.image_paths,
                user_claim=claim.user_claim,
                claim_object=claim.claim_object,
                evidence_standard_met=False,
                evidence_standard_met_reason=(
                    "Automated visual review could not classify this claim."
                ),
                risk_flags="manual_review_required",
                issue_type="unknown",
                object_part="unknown",
                claim_status="not_enough_information",
                claim_status_justification=f"Claim review failed: {exc}",
                supporting_image_ids="none",
                valid_image=True,
                severity="unknown",
            )


ClaimVerifier = VLMClaimVerifier
