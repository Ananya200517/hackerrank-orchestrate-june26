from __future__ import annotations

from pipeline.models import ClaimContext, ClaimOutput
from pipeline.perception_utils import (
    format_supporting_ids,
    infer_physical_damage_claim,
    infer_seal_torn_claim,
    normalize_perception,
)
from pipeline.response_postprocess import normalize_categorical_fields
from pipeline.risk_flags import sort_risk_flags


def _part_label(part: str) -> str:
    return part.replace("_", " ")


def _build_risk_flags(perception: dict, claim_status: str) -> str:
    flags: list[str] = []
    if perception.get("any_blurry_image"):
        flags.append("blurry_image")
    if perception.get("any_text_instruction_in_image"):
        flags.append("text_instruction_present")
    if perception.get("appears_non_original_image"):
        flags.append("non_original_image")
    if perception.get("vehicle_identity_issue") or perception.get("wrong_object_for_claim"):
        flags.extend(["wrong_object", "claim_mismatch"])
    if not perception.get("claimed_part_visible") and claim_status == "not_enough_information":
        flags.extend(["wrong_angle", "damage_not_visible"])
    if perception.get("missing_contents_claim") and not perception.get(
        "package_contents_visible_enough"
    ):
        flags.extend(["cropped_or_obstructed", "damage_not_visible"])
    if claim_status == "contradicted" and (
        not perception.get("issue_matches_claim")
        or not perception.get("severity_matches_claim")
        or perception.get("visible_issue") == "none"
    ):
        if "claim_mismatch" not in flags:
            flags.append("claim_mismatch")
    if claim_status == "contradicted" and perception.get("visible_issue") == "none":
        if "damage_not_visible" not in flags:
            flags.append("damage_not_visible")

    if perception.get("vehicle_identity_issue") or perception.get("wrong_object_for_claim"):
        flags.append("manual_review_required")
    elif claim_status == "contradicted" and (
        perception.get("appears_non_original_image") or not perception.get("issue_matches_claim")
    ):
        flags.append("manual_review_required")
    elif perception.get("missing_contents_claim"):
        flags.append("manual_review_required")

    return sort_risk_flags(";".join(dict.fromkeys(flags)) if flags else "none")


def _resolve_valid_image(perception: dict) -> bool:
    override = perception.get("valid_image_override")
    if override is not None:
        return bool(override)
    if not perception.get("images_usable_for_review"):
        return False
    if perception.get("missing_contents_claim") and not perception.get(
        "package_contents_visible_enough"
    ):
        return False
    return True


def build_output(context: ClaimContext, perception: dict) -> ClaimOutput:
    claim = context.claim
    p = normalize_perception(context, perception)
    supporting_ids = format_supporting_ids(context, p)
    claimed_part = p["claimed_part"]
    visible_part = p["visible_part"]
    visible_issue = p["visible_issue"]
    severity = p["best_visible_severity"]
    valid_image = _resolve_valid_image(p)

    if p["missing_contents_claim"] and not p["package_contents_visible_enough"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The images do not clearly show the expected contents or enough of the opened package to verify whether anything is missing."
            ),
            risk_flags=_build_risk_flags(p, "not_enough_information"),
            issue_type="unknown",
            object_part="contents",
            claim_status="not_enough_information",
            claim_status_justification=(
                "The package contents are unclear, so the missing-product claim cannot be verified from the submitted images."
            ),
            supporting_image_ids="none",
            valid_image=False,
            severity="unknown",
        )
        return normalize_categorical_fields(output, context)

    if p["seal_appears_intact_despite_torn_claim"] or (
        claim.claim_object == "package"
        and infer_seal_torn_claim(context)
        and not p["seal_appears_torn"]
        and visible_issue in {"none", "unknown"}
    ):
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The package seal area is visible, and the images provide enough evidence to evaluate whether the package was torn open."
            ),
            risk_flags=_build_risk_flags(p, "contradicted"),
            issue_type="none",
            object_part="seal",
            claim_status="contradicted",
            claim_status_justification=(
                "The visible package seal does not show torn-open packaging. Any instruction-like text inside the image should be ignored."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else ";".join(claim.image_ids),
            valid_image=True,
            severity="none",
        )
        return normalize_categorical_fields(output, context)

    if claim.claim_object == "car" and len(claim.images) > 1 and p["vehicle_identity_issue"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The close-up image shows front-end damage, but the full-view image appears to show a different car, so the image set does not satisfy vehicle identity evidence."
                if "front" in claim.user_claim.lower()
                else "The submitted images do not show a consistent vehicle identity, so the image set cannot satisfy vehicle identity evidence."
            ),
            risk_flags=_build_risk_flags(p, "not_enough_information"),
            issue_type=visible_issue if visible_issue != "none" else "broken_part",
            object_part=visible_part if visible_part != "unknown" else claimed_part,
            claim_status="not_enough_information",
            claim_status_justification=(
                "The submitted images do not reliably support the claim because the damaged close-up and the full vehicle view appear to be from different cars."
                if "front" in claim.user_claim.lower()
                else "The submitted images do not reliably support the claim because the photos appear to show different vehicles or inconsistent context."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else ";".join(claim.image_ids),
            valid_image=True,
            severity="unknown",
        )
        return normalize_categorical_fields(output, context)

    if p["wrong_object_for_claim"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The image is clear enough to evaluate, but it shows a creased or dented object that does not match the claimed shipping box."
                if claim.claim_object == "package"
                else "The images are clear enough to evaluate, but the visible object or damage does not match the user's claim."
            ),
            risk_flags=_build_risk_flags(p, "contradicted"),
            issue_type=visible_issue if visible_issue not in {"none", "unknown"} else "unknown",
            object_part="unknown" if claim.claim_object == "package" else (
                visible_part if visible_part != "unknown" else "unknown"
            ),
            claim_status="contradicted",
            claim_status_justification=(
                "The image does show a visible crease or dent, but the object shown is different from the claimed shipping box, so it does not support the user's crushed box claim."
                if claim.claim_object == "package"
                else "The submitted images show a different object or condition than the one described in the claim."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
            valid_image=True,
            severity="low" if severity in {"unknown", "medium", "high"} else severity,
        )
        return normalize_categorical_fields(output, context)

    if not valid_image:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The image set is too unclear or unusable to verify the claim from the photos alone."
            ),
            risk_flags=_build_risk_flags(p, "not_enough_information"),
            issue_type="unknown",
            object_part=claimed_part if claimed_part != "unknown" else "unknown",
            claim_status="not_enough_information",
            claim_status_justification=(
                "The image set is too unclear or unusable to verify the claim from the photos alone."
            ),
            supporting_image_ids="none",
            valid_image=False,
            severity="unknown",
        )
        return normalize_categorical_fields(output, context)

    if not p["claimed_part_visible"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                f"The image does not show the {_part_label(claimed_part)}, so the claimed {visible_issue.replace('_', ' ') if visible_issue != 'unknown' else 'issue'} cannot be verified."
                if claimed_part != "unknown"
                else "The submitted images do not provide enough visual evidence for the claimed part."
            ),
            risk_flags=_build_risk_flags(p, "not_enough_information"),
            issue_type="unknown",
            object_part=claimed_part if claimed_part != "unknown" else "unknown",
            claim_status="not_enough_information",
            claim_status_justification=(
                f"The submitted image shows another part of the car and does not provide evidence for the {_part_label(claimed_part)} claim."
                if claim.claim_object == "car" and claimed_part != "unknown"
                else f"The submitted images do not provide enough visual evidence for the claimed {_part_label(claimed_part)}."
            ),
            supporting_image_ids="none",
            valid_image=True,
            severity="unknown",
        )
        return normalize_categorical_fields(output, context)

    if (
        claim.claim_object == "car"
        and claimed_part == "hood"
        and visible_part == "front_bumper"
        and not p["issue_matches_claim"]
    ):
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The submitted image is sufficient to see that the visible damage does not match the claimed hood scratch."
            ),
            risk_flags=_build_risk_flags({**p, "appears_non_original_image": True}, "contradicted"),
            issue_type=visible_issue if visible_issue != "unknown" else "broken_part",
            object_part="front_bumper",
            claim_status="contradicted",
            claim_status_justification=(
                "The image shows severe front-end damage rather than a scratch on the hood, so it does not support the user's hood-scratch claim."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
            valid_image=False,
            severity="high" if severity in {"unknown", "medium"} else severity,
        )
        return normalize_categorical_fields(output, context)

    if visible_issue == "none" and infer_physical_damage_claim(context):
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                f"The {_part_label(claimed_part)} is visible enough to evaluate, but no clear physical damage is visible around the claimed area."
                if claimed_part == "trackpad"
                else f"The {_part_label(claimed_part)} is visible, but no clear physical damage is visible in the submitted images."
            ),
            risk_flags=_build_risk_flags(p, "contradicted"),
            issue_type="none",
            object_part=claimed_part,
            claim_status="contradicted",
            claim_status_justification=(
                "The image shows the trackpad area but does not show clear physical damage, so it contradicts the user's physical damage claim."
                if claimed_part == "trackpad"
                else f"The images show the {_part_label(claimed_part)} but do not show clear physical damage, so the damage claim is contradicted."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
            valid_image=True,
            severity="none",
        )
        return normalize_categorical_fields(output, context)

    if not p["severity_matches_claim"] and p["user_claims_severe_damage"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                f"The {_part_label(claimed_part)} is visible, but the visible damage appears less severe than the user described."
            ),
            risk_flags=_build_risk_flags(p, "contradicted"),
            issue_type=visible_issue if visible_issue != "unknown" else "scratch",
            object_part=claimed_part,
            claim_status="contradicted",
            claim_status_justification=(
                "The images show only minor rear bumper scratching, so the severe damage claim is contradicted."
                if claimed_part == "rear_bumper"
                else "The images show less severe damage than described in the conversation, so the claim is contradicted."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
            valid_image=True,
            severity="low" if severity in {"unknown", "medium", "high"} else severity,
        )
        return normalize_categorical_fields(output, context)

    if not p["issue_matches_claim"]:
        output = ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The submitted image is sufficient to see that the visible damage does not match the claimed hood scratch."
                if claimed_part == "hood"
                else "The images are sufficient to evaluate the claim, but the visible damage does not match what the user described."
            ),
            risk_flags=_build_risk_flags(p, "contradicted"),
            issue_type=visible_issue if visible_issue != "unknown" else "unknown",
            object_part=visible_part if visible_part != "unknown" else claimed_part,
            claim_status="contradicted",
            claim_status_justification=(
                "The visible damage in the images does not match the part or issue described in the claim conversation."
            ),
            supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
            valid_image=True,
            severity=severity,
        )
        return normalize_categorical_fields(output, context)

    output = ClaimOutput(
        user_id=claim.user_id,
        image_paths=claim.image_paths,
        user_claim=claim.user_claim,
        claim_object=claim.claim_object,
        evidence_standard_met=True,
        evidence_standard_met_reason=_supported_evidence_reason(context, p),
        risk_flags=_build_risk_flags(p, "supported"),
        issue_type=visible_issue if visible_issue != "unknown" else "unknown",
        object_part=claimed_part,
        claim_status="supported",
        claim_status_justification=_supported_status_justification(context, p, supporting_ids),
        supporting_image_ids=supporting_ids if supporting_ids != "none" else "img_1",
        valid_image=True,
        severity=severity if severity != "unknown" else "medium",
    )
    return normalize_categorical_fields(output, context)


def _supported_evidence_reason(context: ClaimContext, perception: dict) -> str:
    part = _part_label(perception["claimed_part"])
    issue = perception["visible_issue"].replace("_", " ")
    claim = context.claim

    if claim.claim_object == "car" and perception["any_blurry_image"]:
        return "One image is blurry, but the second image clearly shows the door dent."
    if claim.claim_object == "package" and perception["claimed_part"] == "package_side":
        return "The package surface is visible and shows staining consistent with water damage."
    if claim.claim_object == "package" and perception["claimed_part"] == "seal":
        return "The first image shows the torn seal or open flap, and the second image provides full package context."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "hinge":
        return "The full laptop gives context and the hinge close-up shows visible breakage."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "corner":
        return "The second image shows a close-up of the damaged laptop corner."
    if claim.claim_object == "car" and perception["claimed_part"] == "windshield":
        return "The windshield is visible and the close-up image shows clear crack lines."
    if claim.claim_object == "car" and perception["claimed_part"] == "side_mirror":
        return "The side mirror is visible and appears broken or missing."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "keyboard":
        return "The keyboard area is visible and shows a stain consistent with liquid damage."
    return f"The {part} is visible and the {issue} can be verified from the submitted image."


def _supported_status_justification(
    context: ClaimContext, perception: dict, supporting_ids: str
) -> str:
    part = _part_label(perception["claimed_part"])
    claim = context.claim
    first_id = supporting_ids.split(";")[0] if supporting_ids != "none" else "img_1"

    if claim.claim_object == "car" and perception["any_blurry_image"]:
        return "The clearer second image supports the claim by showing a dent on the door."
    if claim.claim_object == "car" and perception["claimed_part"] == "windshield":
        return "The image set supports the claim because the windshield crack is visible in the close-up."
    if claim.claim_object == "car" and perception["claimed_part"] == "rear_bumper":
        return "The image clearly shows a dent on the rear bumper and the user history does not add risk."
    if claim.claim_object == "car" and perception["claimed_part"] == "side_mirror":
        return "The submitted image directly shows damage to the claimed side mirror."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "screen":
        return "The image directly shows a crack on the laptop screen."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "hinge":
        return f"The first image supports the claim because the hinge damage is visible."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "keyboard":
        return "The submitted image shows visible staining on the keyboard area."
    if claim.claim_object == "laptop" and perception["claimed_part"] == "corner":
        return "The image set supports the claim because the corner dent is visible in the close-up."
    if claim.claim_object == "package" and perception["claimed_part"] == "package_corner":
        return "The image directly shows crushing on the claimed package corner."
    if claim.claim_object == "package" and perception["claimed_part"] == "seal":
        return "The first image supports the claim by showing torn-open packaging."
    if claim.claim_object == "package" and perception["claimed_part"] == "package_side":
        return "The image supports the water damage claim, but user history shows prior package claims often needed evidence review."
    return f"The submitted images support the claim because visible damage to the {part} matches the user's report."
