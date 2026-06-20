from __future__ import annotations

RISK_FLAG_ORDER = [
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
]


def sort_risk_flags(flags: str) -> str:
    if flags == "none" or not flags.strip():
        return "none"
    tokens = [token for token in flags.split(";") if token.strip()]
    order = {flag: index for index, flag in enumerate(RISK_FLAG_ORDER)}
    return ";".join(sorted(tokens, key=lambda token: order.get(token, len(RISK_FLAG_ORDER))))
