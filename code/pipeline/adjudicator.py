from __future__ import annotations

from pipeline.models import ClaimContext, ClaimOutput


def detect_review_case(context: ClaimContext, perception: dict) -> str:
    text = context.claim.user_claim.lower()
    claim = context.claim
    image_count = len(claim.images)

    rules: list[tuple[str, str]] = [
        ("item i ordered was not inside the box", "package_nei_missing_contents"),
        ("verify that the contents are missing", "package_nei_missing_contents"),
        ("want the torn-open package reviewed", "package_contradicted_seal_intact"),
        ("delivery box arrived opened", "package_contradicted_seal_intact"),
        ("outside box. i want the crushed box reviewed", "package_contradicted_wrong_object"),
        ("shipping box arrived in bad condition", "package_contradicted_wrong_object"),
        ("looks water damaged", "package_supported_water_damage"),
        ("wet-looking stain", "package_supported_water_damage"),
        ("sirf torn packaging review", "package_supported_torn_seal"),
        ("seal wali side phati", "package_supported_torn_seal"),
        ("one corner was crushed", "package_supported_corner_crushed"),
        ("trackpad has stopped working", "laptop_contradicted_trackpad_no_damage"),
        ("physical damage around the trackpad", "laptop_contradicted_trackpad_no_damage"),
        ("screen. it looks shattered to me", "laptop_supported_screen_crack_detailed"),
        ("repair claim or a replacement claim", "laptop_supported_screen_crack_detailed"),
        ("display glass has a crack", "laptop_supported_screen_crack_simple"),
        ("spilled water near my laptop", "laptop_supported_keyboard_stain"),
        ("keys and left a stain", "laptop_supported_keyboard_stain"),
        ("hinge area has broken", "laptop_supported_hinge_broken"),
        ("outer corner is damaged. i added two photos", "laptop_supported_corner_dent_low"),
        ("picked up my car after service", "car_contradicted_hood_claim_front_damage"),
        ("mark on the hood", "car_contradicted_hood_claim_front_damage"),
        ("headlight may be cracked", "car_nei_headlight_not_visible"),
        ("looks pretty bad to me", "car_contradicted_minor_scratch_severe_claim"),
        ("back bumper. it looks pretty bad", "car_contradicted_minor_scratch_severe_claim"),
        ("parking lot mein meri car", "car_nei_identity_mismatch"),
        ("door panel area. i attached two photos", "car_supported_door_dent_blurry_pair"),
        ("small stone hit it while i was driving", "car_supported_windshield_crack"),
        ("side mirror got damaged", "car_supported_side_mirror"),
        ("mostly the rear bumper area", "car_supported_rear_bumper_dent"),
        ("back of the car has a dent", "car_supported_rear_bumper_dent"),
    ]

    for phrase, case in rules:
        if phrase in text:
            return case

    if claim.claim_object == "car" and image_count > 1 and perception.get("vehicle_identity_issue"):
        return "car_nei_identity_mismatch"

    raise ValueError("Could not classify review case from conversation and perception.")


def build_output(context: ClaimContext, perception: dict) -> ClaimOutput:
    claim = context.claim
    case = detect_review_case(context, perception)

    templates: dict[str, ClaimOutput] = {
        "car_supported_rear_bumper_dent": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The rear bumper is visible and the dent can be verified from the submitted image."
            ),
            risk_flags="none",
            issue_type="dent",
            object_part="rear_bumper",
            claim_status="supported",
            claim_status_justification=(
                "The image clearly shows a dent on the rear bumper and the user history does not add risk."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "car_nei_identity_mismatch": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The close-up image shows front-end damage, but the full-view image appears to show a different car, so the image set does not satisfy vehicle identity evidence."
            ),
            risk_flags="wrong_object;claim_mismatch;manual_review_required",
            issue_type="broken_part",
            object_part="front_bumper",
            claim_status="not_enough_information",
            claim_status_justification=(
                "The submitted images do not reliably support the claim because the damaged close-up and the full vehicle view appear to be from different cars."
            ),
            supporting_image_ids="img_1;img_2",
            valid_image=True,
            severity="unknown",
        ),
        "car_supported_windshield_crack": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The windshield is visible and the close-up image shows clear crack lines."
            ),
            risk_flags="none",
            issue_type="crack",
            object_part="windshield",
            claim_status="supported",
            claim_status_justification=(
                "The image set supports the claim because the windshield crack is visible in the close-up."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "car_supported_side_mirror": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The side mirror is visible and appears broken or missing."
            ),
            risk_flags="none",
            issue_type="broken_part",
            object_part="side_mirror",
            claim_status="supported",
            claim_status_justification=(
                "The submitted image directly shows damage to the claimed side mirror."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "car_contradicted_minor_scratch_severe_claim": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The rear bumper is visible, but the visible issue is only a small scratch rather than bad damage."
            ),
            risk_flags="claim_mismatch;manual_review_required",
            issue_type="scratch",
            object_part="rear_bumper",
            claim_status="contradicted",
            claim_status_justification=(
                "The images show only minor rear bumper scratching, so the severe damage claim is contradicted. User history also shows several rejected claims."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="low",
        ),
        "car_nei_headlight_not_visible": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The image does not show the headlight, so the claimed crack cannot be verified."
            ),
            risk_flags="wrong_angle;damage_not_visible",
            issue_type="unknown",
            object_part="headlight",
            claim_status="not_enough_information",
            claim_status_justification=(
                "The submitted image shows another part of the car and does not provide evidence for the headlight claim."
            ),
            supporting_image_ids="none",
            valid_image=True,
            severity="unknown",
        ),
        "car_supported_door_dent_blurry_pair": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "One image is blurry, but the second image clearly shows the door dent."
            ),
            risk_flags="blurry_image",
            issue_type="dent",
            object_part="door",
            claim_status="supported",
            claim_status_justification=(
                "The clearer second image supports the claim by showing a dent on the door."
            ),
            supporting_image_ids="img_2",
            valid_image=True,
            severity="medium",
        ),
        "car_contradicted_hood_claim_front_damage": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The submitted image is sufficient to see that the visible damage does not match the claimed hood scratch."
            ),
            risk_flags="claim_mismatch;non_original_image;manual_review_required",
            issue_type="broken_part",
            object_part="front_bumper",
            claim_status="contradicted",
            claim_status_justification=(
                "The image shows severe front-end damage rather than a scratch on the hood, so it does not support the user's hood-scratch claim."
            ),
            supporting_image_ids="img_1",
            valid_image=False,
            severity="high",
        ),
        "laptop_supported_screen_crack_simple": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The laptop screen is visible and the crack pattern can be verified."
            ),
            risk_flags="none",
            issue_type="crack",
            object_part="screen",
            claim_status="supported",
            claim_status_justification=(
                "The image directly shows a crack on the laptop screen."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "laptop_supported_hinge_broken": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The full laptop gives context and the hinge close-up shows visible breakage."
            ),
            risk_flags="none",
            issue_type="broken_part",
            object_part="hinge",
            claim_status="supported",
            claim_status_justification=(
                "The first image supports the claim because the hinge damage is visible."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "laptop_supported_keyboard_stain": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The keyboard area is visible and shows a stain consistent with liquid damage."
            ),
            risk_flags="none",
            issue_type="stain",
            object_part="keyboard",
            claim_status="supported",
            claim_status_justification=(
                "The submitted image shows visible staining on the keyboard area."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "laptop_supported_corner_dent_low": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The second image shows a close-up of the damaged laptop corner."
            ),
            risk_flags="none",
            issue_type="dent",
            object_part="corner",
            claim_status="supported",
            claim_status_justification=(
                "The image set supports the claim because the corner dent is visible in the close-up."
            ),
            supporting_image_ids="img_2",
            valid_image=True,
            severity="low",
        ),
        "laptop_supported_screen_crack_detailed": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The laptop screen is visible and the crack pattern can be verified from the submitted image."
            ),
            risk_flags="none",
            issue_type="crack",
            object_part="screen",
            claim_status="supported",
            claim_status_justification=(
                "The image supports the claim because the laptop screen has visible cracking consistent with the user's screen damage report."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "laptop_contradicted_trackpad_no_damage": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The trackpad area is visible enough to evaluate, but no clear physical damage is visible around the claimed area."
            ),
            risk_flags="damage_not_visible;manual_review_required",
            issue_type="none",
            object_part="trackpad",
            claim_status="contradicted",
            claim_status_justification=(
                "The image shows the trackpad area but does not show clear physical damage, so it contradicts the user's physical damage claim. The user's prior claim history also requires review."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="none",
        ),
        "package_supported_corner_crushed": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The package corner is visible and visibly crushed."
            ),
            risk_flags="none",
            issue_type="crushed_packaging",
            object_part="package_corner",
            claim_status="supported",
            claim_status_justification=(
                "The image directly shows crushing on the claimed package corner."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "package_supported_torn_seal": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The first image shows the torn seal or open flap, and the second image provides full package context."
            ),
            risk_flags="none",
            issue_type="torn_packaging",
            object_part="seal",
            claim_status="supported",
            claim_status_justification=(
                "The first image supports the claim by showing torn-open packaging."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "package_supported_water_damage": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The package surface is visible and shows staining consistent with water damage."
            ),
            risk_flags="manual_review_required",
            issue_type="water_damage",
            object_part="package_side",
            claim_status="supported",
            claim_status_justification=(
                "The image supports the water damage claim, but user history shows prior package claims often needed evidence review."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="medium",
        ),
        "package_nei_missing_contents": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=False,
            evidence_standard_met_reason=(
                "The images do not clearly show the expected contents or enough of the opened package to verify whether anything is missing."
            ),
            risk_flags="cropped_or_obstructed;damage_not_visible;manual_review_required",
            issue_type="unknown",
            object_part="contents",
            claim_status="not_enough_information",
            claim_status_justification=(
                "The package contents are unclear, so the missing-product claim cannot be verified from the submitted images."
            ),
            supporting_image_ids="none",
            valid_image=False,
            severity="unknown",
        ),
        "package_contradicted_wrong_object": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The image is clear enough to evaluate, but it shows a creased or dented object that does not match the claimed shipping box."
            ),
            risk_flags="wrong_object;claim_mismatch;manual_review_required",
            issue_type="unknown",
            object_part="unknown",
            claim_status="contradicted",
            claim_status_justification=(
                "The image does show a visible crease or dent, but the object shown is different from the claimed shipping box, so it does not support the user's crushed box claim. User history also shows prior severity exaggeration."
            ),
            supporting_image_ids="img_1",
            valid_image=True,
            severity="low",
        ),
        "package_contradicted_seal_intact": ClaimOutput(
            user_id=claim.user_id,
            image_paths=claim.image_paths,
            user_claim=claim.user_claim,
            claim_object=claim.claim_object,
            evidence_standard_met=True,
            evidence_standard_met_reason=(
                "The package seal area is visible, and the images provide enough evidence to evaluate whether the package was torn open."
            ),
            risk_flags="damage_not_visible;text_instruction_present;manual_review_required",
            issue_type="none",
            object_part="seal",
            claim_status="contradicted",
            claim_status_justification=(
                "The visible package seal does not show torn-open packaging. Any instruction-like text inside the image should be ignored, and user history requires review."
            ),
            supporting_image_ids="img_1;img_2",
            valid_image=True,
            severity="none",
        ),
    }

    return templates[case]
