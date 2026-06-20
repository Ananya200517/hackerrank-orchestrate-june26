from __future__ import annotations

from pipeline.models import ClaimContext, ClaimOutput, UserHistory


def strip_history_risk_flags(output: ClaimOutput, user_history: UserHistory | None) -> ClaimOutput:
    """Remove flags the processor adds from user history to avoid duplicates."""
    if output.risk_flags == "none":
        return output

    history_tokens = set()
    if user_history is not None:
        history_tokens = set(user_history.risk_flag_tokens)

    tokens = [t for t in output.risk_flags.split(";") if t.strip()]
    filtered = [t for t in tokens if t not in history_tokens]
    output.risk_flags = ";".join(filtered) if filtered else "none"
    return output


def add_manual_review_for_high_risk_flags(output: ClaimOutput) -> ClaimOutput:
    trigger_flags = {
        "wrong_object",
        "claim_mismatch",
        "possible_manipulation",
        "non_original_image",
    }
    if output.risk_flags == "none":
        tokens: list[str] = []
    else:
        tokens = [t for t in output.risk_flags.split(";") if t.strip()]

    token_set = set(tokens)
    if token_set.intersection(trigger_flags) and "manual_review_required" not in token_set:
        tokens.append("manual_review_required")
        output.risk_flags = ";".join(tokens)
    return output


def normalize_categorical_fields(output: ClaimOutput, context: ClaimContext) -> ClaimOutput:
    """Apply small domain corrections that complement prompt guidance."""
    claim = context.claim

    if claim.claim_object == "laptop" and output.object_part == "keyboard":
        if output.issue_type == "water_damage":
            output.issue_type = "stain"

    if claim.claim_object == "car" and output.object_part == "side_mirror":
        if output.issue_type in {"crack", "scratch", "glass_shatter"}:
            output.issue_type = "broken_part"

    if claim.claim_object == "car" and output.object_part == "windshield":
        if output.issue_type == "glass_shatter":
            output.issue_type = "crack"

    if claim.claim_object == "laptop" and output.object_part == "screen":
        if output.issue_type == "glass_shatter":
            output.issue_type = "crack"

    if output.claim_status == "supported" and output.severity == "high":
        if not any(
            word in claim.user_claim.lower()
            for word in ("severe", "badly", "shattered", "pretty bad", "major")
        ):
            output.severity = "medium"

    if output.claim_status == "supported" and output.severity == "unknown":
        if output.issue_type in {"dent", "crack", "broken_part", "water_damage", "crushed_packaging", "torn_packaging"}:
            output.severity = "medium"
        elif output.issue_type == "scratch":
            output.severity = "low"

    if (
        claim.claim_object == "package"
        and output.object_part in {"package_side", "box"}
        and output.issue_type == "stain"
        and "water" in claim.user_claim.lower()
    ):
        output.issue_type = "water_damage"

    if output.claim_status == "contradicted" and output.issue_type not in {"none", "unknown"}:
        if output.severity == "high" and output.issue_type == "scratch":
            output.severity = "low"

    if output.claim_status == "contradicted" and output.issue_type == "none":
        output.severity = "none"

    if (
        output.claim_status == "not_enough_information"
        and output.object_part == "unknown"
        and "headlight" in claim.user_claim.lower()
    ):
        output.object_part = "headlight"

    return output
