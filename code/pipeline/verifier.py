from __future__ import annotations

import time

from pipeline.models import ClaimContext, ClaimOutput
from pipeline.prompts import parse_verification_response
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
    """Vision-language model backed claim verifier."""

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

        attempts = self.settings.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                raw_response = self.client.analyze_claim(context)
                return parse_verification_response(raw_response, context)
            except Exception as exc:  # noqa: BLE001 - retry on provider/parse failures
                last_error = exc
                self.usage.errors += 1
                if attempt < attempts - 1:
                    time.sleep(1.5 * (attempt + 1))

        return ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "Automated visual review failed after retries."
            ),
            risk_flags="manual_review_required",
            issue_type="unknown",
            object_part="unknown",
            claim_status="not_enough_information",
            claim_status_justification=(
                f"VLM verification failed: {last_error}"
            ),
            supporting_image_ids="none",
            valid_image=True,
            severity="unknown",
        )


# Backward-compatible alias used by earlier skeleton code.
ClaimVerifier = VLMClaimVerifier
