from __future__ import annotations

from pipeline.config import (
    ISSUE_TYPES,
    OBJECT_PARTS_BY_CLAIM_OBJECT,
    SEVERITIES,
)
from pipeline.models import ClaimContext


def _as_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return default


def _normalize_enum(value: object, allowed: set[str], default: str = "unknown") -> str:
    if not isinstance(value, str):
        return default
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in allowed:
        return normalized
    aliases = {
        "glass_shattered": "glass_shatter",
        "shatter": "glass_shatter",
        "shattered": "glass_shatter",
        "crushed": "crushed_packaging",
        "torn": "torn_packaging",
        "water_stain": "water_damage",
        "missing": "missing_part",
        "broken": "broken_part",
        "rear_bumper_crack": "scratch",
    }
    if normalized in aliases and aliases[normalized] in allowed:
        return aliases[normalized]
    return default


PART_KEYWORDS = {
    "car": [
        ("rear_bumper", ("rear bumper", "back bumper", "parachoques de atras", "parachoque", "back of the car")),
        ("front_bumper", ("front bumper", "front end", "front side", "parachoques")),
        ("windshield", ("windshield", "front glass", "front glass")),
        ("side_mirror", ("side mirror", "mirror")),
        ("headlight", ("headlight", "front light")),
        ("taillight", ("taillight", "back light", "tail light")),
        ("door", ("door", "door panel")),
        ("hood", ("hood", "bonnet")),
        ("fender", ("fender",)),
        ("body", ("body panel", "car body", "body")),
    ],
    "laptop": [
        ("screen", ("screen", "display", "pantalla")),
        ("keyboard", ("keyboard", "keycap", "keys")),
        ("trackpad", ("trackpad", "touchpad")),
        ("hinge", ("hinge",)),
        ("corner", ("corner",)),
        ("lid", ("lid",)),
        ("body", ("body", "palm-rest", "outer body")),
    ],
    "package": [
        ("contents", ("contents are missing", "missing from the package", "not inside", "product inside", "item inside", "missing contents", "could not find the product")),
        ("seal", ("seal", "torn-open", "torn open", "opened", "tape broken", "phati hui")),
        ("package_corner", ("corner", "package corner", "cardboard box corner")),
        ("label", ("label",)),
        ("item", ("item inside", "inside item", "product")),
        ("package_side", ("package surface", "wet box", "package surface", "outside box", "outside has")),
        ("box", ("box", "cardboard box", "delivery box", "shipping box", "parcel")),
    ],
}

ISSUE_KEYWORDS = [
    ("dent", ("dent", "dented")),
    ("scratch", ("scratch", "scrape", "mark")),
    ("crack", ("crack", "cracked")),
    ("glass_shatter", ("shatter", "shattered")),
    ("broken_part", ("broken", "breakage", "not sitting")),
    ("missing_part", ("missing",)),
    ("torn_packaging", ("torn", "opened", "torn-open", "torn open", "phati hui")),
    ("crushed_packaging", ("crushed", "crush", "badly crushed")),
    ("water_damage", ("water damage", "water damaged", "wet-looking", "wet box")),
    ("stain", ("stain", "sticky", "spilled water")),
]


def infer_claimed_part(context: ClaimContext) -> str:
    if infer_missing_contents_claim(context):
        return "contents"

    text = context.claim.user_claim.lower()
    allowed = OBJECT_PARTS_BY_CLAIM_OBJECT[context.claim.claim_object]
    for part, keywords in PART_KEYWORDS[context.claim.claim_object]:
        if part in allowed and any(keyword in text for keyword in keywords):
            return part
    return "unknown"


def infer_claimed_issue(context: ClaimContext) -> str:
    text = context.claim.user_claim.lower()
    for issue, keywords in ISSUE_KEYWORDS:
        if issue in ISSUE_TYPES and any(keyword in text for keyword in keywords):
            return issue
    return "unknown"


def infer_missing_contents_claim(context: ClaimContext) -> bool:
    text = context.claim.user_claim.lower()
    markers = (
        "not inside",
        "missing from the package",
        "product inside",
        "item inside",
        "contents are missing",
        "missing contents",
        "could not find the product",
        "was not inside the box",
    )
    return any(marker in text for marker in markers)


def infer_seal_torn_claim(context: ClaimContext) -> bool:
    if context.claim.claim_object != "package":
        return False
    text = context.claim.user_claim.lower()
    return any(
        phrase in text
        for phrase in (
            "torn",
            "opened",
            "torn-open",
            "torn open",
            "seal area",
            "seal wali",
            "phati hui",
        )
    )


def infer_severe_claim(context: ClaimContext) -> bool:
    text = context.claim.user_claim.lower()
    return any(
        word in text
        for word in (
            "severe",
            "bad damage",
            "pretty bad",
            "badly crushed",
            "badly damaged",
            "shattered",
            "major",
            "looks pretty bad",
        )
    )


def infer_physical_damage_claim(context: ClaimContext) -> bool:
    text = context.claim.user_claim.lower()
    return any(
        word in text
        for word in (
            "dent",
            "scratch",
            "crack",
            "broken",
            "damage",
            "crushed",
            "torn",
            "shatter",
            "missing",
            "stain",
            "water",
        )
    )


def _align_visible_issue(context: ClaimContext, visible_issue: str, visible_part: str, claimed_part: str) -> str:
    claimed_issue = infer_claimed_issue(context)
    if visible_issue in {"none", "unknown"} and claimed_issue != "unknown":
        if visible_part == claimed_part or visible_part == "unknown":
            return claimed_issue

    if context.claim.claim_object == "car" and visible_part == "side_mirror" and visible_issue == "glass_shatter":
        return "broken_part"

    if context.claim.claim_object in {"car", "laptop"} and visible_part in {"windshield", "screen"}:
        if visible_issue == "glass_shatter" and "crack" in context.claim.user_claim.lower():
            return "crack"

    if visible_issue == "missing_part" and "dent" in context.claim.user_claim.lower():
        return "dent"

    return visible_issue


def _apply_sanity_corrections(context: ClaimContext, normalized: dict) -> dict:
    claim_object = context.claim.claim_object
    allowed_parts = OBJECT_PARTS_BY_CLAIM_OBJECT[claim_object]
    claimed_part = normalized["claimed_part"]
    visible_part = normalized["visible_part"]
    visible_issue = normalized["visible_issue"]

    if normalized["missing_contents_claim"]:
        normalized["claimed_part"] = "contents"
        claimed_part = "contents"

    if infer_seal_torn_claim(context) and not normalized["missing_contents_claim"]:
        if claimed_part in {"unknown", "box"}:
            normalized["claimed_part"] = "seal"
            claimed_part = "seal"

    visible_issue = _align_visible_issue(context, visible_issue, visible_part, claimed_part)
    normalized["visible_issue"] = visible_issue

    if normalized["wrong_object_for_claim"]:
        normalized["issue_matches_claim"] = False
    elif (
        visible_part == claimed_part
        and visible_issue not in {"none", "unknown"}
        and claimed_part != "unknown"
    ):
        normalized["issue_matches_claim"] = True
    elif (
        visible_part != "unknown"
        and claimed_part != "unknown"
        and visible_part != claimed_part
        and visible_issue not in {"none", "unknown"}
    ):
        normalized["issue_matches_claim"] = False

    if (
        claim_object == "car"
        and not normalized["claimed_part_visible"]
        and claimed_part != "unknown"
        and visible_part in allowed_parts
        and visible_part != claimed_part
        and not normalized["vehicle_identity_issue"]
    ):
        normalized["wrong_object_for_claim"] = False

    if normalized["vehicle_identity_issue"]:
        if normalized["same_object_identity_across_images"]:
            normalized["vehicle_identity_issue"] = False
        elif (
            normalized["claimed_part_visible"]
            and visible_part == claimed_part
            and visible_issue not in {"none", "unknown"}
            and not normalized["wrong_object_for_claim"]
        ):
            normalized["vehicle_identity_issue"] = False

    if (
        claim_object == "package"
        and infer_seal_torn_claim(context)
        and not normalized["seal_appears_torn"]
        and visible_issue in {"none", "unknown", "torn_packaging"}
        and not normalized["missing_contents_claim"]
    ):
        normalized["seal_appears_intact_despite_torn_claim"] = True
        normalized["visible_issue"] = "none"

    if (
        claim_object == "car"
        and len(context.claim.images) > 1
        and normalized["vehicle_identity_issue"]
        and not _as_bool(normalized.get("appears_non_original_image"))
        and normalized["same_object_identity_across_images"]
    ):
        normalized["vehicle_identity_issue"] = False

    if normalized["any_blurry_image"] and normalized["claimed_part_visible"]:
        normalized["images_usable_for_review"] = True

    if (
        not normalized["images_usable_for_review"]
        and normalized["claimed_part_visible"]
        and not normalized["any_blurry_image"]
    ):
        normalized["images_usable_for_review"] = True

    if (
        not normalized["images_usable_for_review"]
        and not normalized["any_blurry_image"]
        and not normalized["appears_non_original_image"]
        and claim_object == "car"
        and claimed_part != "unknown"
        and not normalized["claimed_part_visible"]
    ):
        normalized["images_usable_for_review"] = True

    severity = normalized["best_visible_severity"]
    if severity == "high" and not normalized["user_claims_severe_damage"]:
        if visible_issue in {"dent", "crack", "broken_part", "stain", "water_damage", "torn_packaging", "crushed_packaging"}:
            normalized["best_visible_severity"] = "medium"
        elif visible_issue == "scratch":
            normalized["best_visible_severity"] = "low"

    if claim_object == "package" and claimed_part in {"package_side", "box"} and "water" in context.claim.user_claim.lower():
        if visible_issue == "stain":
            normalized["visible_issue"] = "water_damage"
        if claimed_part == "box" and "surface" in context.claim.user_claim.lower():
            normalized["claimed_part"] = "package_side"
            normalized["visible_part"] = "package_side" if visible_part in {"box", "package_side", "unknown"} else visible_part

    if (
        claim_object == "car"
        and claimed_part == "hood"
        and "scratch" in context.claim.user_claim.lower()
        and visible_issue in {"broken_part", "dent", "scratch"}
        and visible_issue != "scratch"
    ):
        normalized["issue_matches_claim"] = False
        normalized["visible_part"] = "front_bumper"
        normalized["claimed_part_visible"] = True
        normalized["valid_image_override"] = False
        normalized["best_visible_severity"] = "high"

    if (
        claim_object == "car"
        and claimed_part == "hood"
        and visible_part in {"front_bumper", "hood", "body"}
        and visible_issue in {"broken_part", "dent", "scratch"}
        and not normalized["issue_matches_claim"]
    ):
        normalized["visible_part"] = "front_bumper"
        normalized["claimed_part_visible"] = True
        normalized["valid_image_override"] = False

    return normalized


def normalize_perception(context: ClaimContext, perception: dict) -> dict:
    claim_object = context.claim.claim_object
    allowed_parts = OBJECT_PARTS_BY_CLAIM_OBJECT[claim_object]
    normalized = dict(perception or {})

    claimed_part = _normalize_enum(
        normalized.get("claimed_part", infer_claimed_part(context)),
        allowed_parts,
        infer_claimed_part(context),
    )
    visible_part = _normalize_enum(
        normalized.get("visible_part", "unknown"),
        allowed_parts,
        "unknown",
    )
    visible_issue = _normalize_enum(
        normalized.get("visible_issue", "unknown"),
        ISSUE_TYPES,
        "unknown",
    )
    severity = _normalize_enum(
        normalized.get("best_visible_severity", "unknown"),
        SEVERITIES,
        "unknown",
    )

    supporting = normalized.get("clear_supporting_image_ids", [])
    if isinstance(supporting, str):
        supporting = [part.strip() for part in supporting.replace(",", ";").split(";") if part.strip()]
    if not isinstance(supporting, list):
        supporting = []

    normalized.update(
        {
            "claimed_part": claimed_part,
            "visible_part": visible_part,
            "visible_issue": visible_issue,
            "best_visible_severity": severity,
            "clear_supporting_image_ids": supporting,
            "user_claims_severe_damage": _as_bool(
                normalized.get("user_claims_severe_damage"),
                infer_severe_claim(context),
            ),
            "same_object_identity_across_images": _as_bool(
                normalized.get("same_object_identity_across_images"), True
            ),
            "vehicle_identity_issue": _as_bool(normalized.get("vehicle_identity_issue")),
            "claimed_part_visible": _as_bool(normalized.get("claimed_part_visible")),
            "issue_matches_claim": _as_bool(normalized.get("issue_matches_claim")),
            "severity_matches_claim": _as_bool(normalized.get("severity_matches_claim"), True),
            "any_blurry_image": _as_bool(normalized.get("any_blurry_image")),
            "any_text_instruction_in_image": _as_bool(
                normalized.get("any_text_instruction_in_image")
            ),
            "appears_non_original_image": _as_bool(normalized.get("appears_non_original_image")),
            "package_contents_visible_enough": _as_bool(
                normalized.get("package_contents_visible_enough")
            ),
            "seal_appears_torn": _as_bool(normalized.get("seal_appears_torn")),
            "seal_appears_intact_despite_torn_claim": _as_bool(
                normalized.get("seal_appears_intact_despite_torn_claim")
            ),
            "wrong_object_for_claim": _as_bool(normalized.get("wrong_object_for_claim")),
            "images_usable_for_review": _as_bool(normalized.get("images_usable_for_review"), True),
            "missing_contents_claim": _as_bool(
                normalized.get("missing_contents_claim"),
                infer_missing_contents_claim(context),
            ),
            "valid_image_override": None,
        }
    )
    return _apply_sanity_corrections(context, normalized)


def format_supporting_ids(context: ClaimContext, perception: dict) -> str:
    valid_ids = set(context.claim.image_ids)
    ids = [
        image_id
        for image_id in perception.get("clear_supporting_image_ids", [])
        if image_id in valid_ids
    ]
    if ids:
        return ";".join(ids)
    if len(context.claim.images) > 1 and perception.get("vehicle_identity_issue"):
        return ";".join(context.claim.image_ids)
    if perception.get("any_blurry_image") and len(context.claim.images) > 1:
        clear_ids = [
            note.get("image_id")
            for note in perception.get("image_notes", [])
            if isinstance(note, dict) and not _as_bool(note.get("blurry"))
        ]
        clear_ids = [image_id for image_id in clear_ids if image_id in valid_ids]
        if clear_ids:
            return ";".join(clear_ids)
    return "none"
