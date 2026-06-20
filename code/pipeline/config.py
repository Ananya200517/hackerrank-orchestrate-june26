from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CLAIMS_PATH = REPO_ROOT / "dataset" / "claims.csv"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "dataset" / "output.csv"
DEFAULT_USER_HISTORY_PATH = REPO_ROOT / "dataset" / "user_history.csv"
DEFAULT_EVIDENCE_REQUIREMENTS_PATH = REPO_ROOT / "dataset" / "evidence_requirements.csv"
DEFAULT_SAMPLE_CLAIMS_PATH = REPO_ROOT / "dataset" / "sample_claims.csv"

OUTPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
    "evidence_standard_met",
    "evidence_standard_met_reason",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "claim_status_justification",
    "supporting_image_ids",
    "valid_image",
    "severity",
]

INPUT_COLUMNS = [
    "user_id",
    "image_paths",
    "user_claim",
    "claim_object",
]

CLAIM_OBJECTS = {"car", "laptop", "package"}

CLAIM_STATUSES = {"supported", "contradicted", "not_enough_information"}

ISSUE_TYPES = {
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_part",
    "missing_part",
    "torn_packaging",
    "crushed_packaging",
    "water_damage",
    "stain",
    "none",
    "unknown",
}

SEVERITIES = {"none", "low", "medium", "high", "unknown"}

RISK_FLAGS = {
    "none",
    "blurry_image",
    "cropped_or_obstructed",
    "low_light_or_glare",
    "wrong_angle",
    "wrong_object",
    "wrong_object_part",
    "damage_not_visible",
    "claim_mismatch",
    "possible_manipulation",
    "non_original_image",
    "text_instruction_present",
    "user_history_risk",
    "manual_review_required",
}

CAR_OBJECT_PARTS = {
    "front_bumper",
    "rear_bumper",
    "door",
    "hood",
    "windshield",
    "side_mirror",
    "headlight",
    "taillight",
    "fender",
    "quarter_panel",
    "body",
    "unknown",
}

LAPTOP_OBJECT_PARTS = {
    "screen",
    "keyboard",
    "trackpad",
    "hinge",
    "lid",
    "corner",
    "port",
    "base",
    "body",
    "unknown",
}

PACKAGE_OBJECT_PARTS = {
    "box",
    "package_corner",
    "package_side",
    "seal",
    "label",
    "contents",
    "item",
    "unknown",
}

OBJECT_PARTS_BY_CLAIM_OBJECT = {
    "car": CAR_OBJECT_PARTS,
    "laptop": LAPTOP_OBJECT_PARTS,
    "package": PACKAGE_OBJECT_PARTS,
}
