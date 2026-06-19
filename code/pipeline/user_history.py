from __future__ import annotations

from pipeline.models import UserHistory


def lookup_user_history(
    user_id: str,
    history_by_user: dict[str, UserHistory],
) -> UserHistory | None:
    return history_by_user.get(user_id)


def merge_history_risk_flags(existing_flags: list[str], user_history: UserHistory | None) -> list[str]:
    merged = list(existing_flags)
    if user_history is None:
        return merged

    for flag in user_history.risk_flag_tokens:
        if flag not in merged:
            merged.append(flag)
    return merged


def format_risk_flags(flags: list[str]) -> str:
    if not flags:
        return "none"
    return ";".join(flags)
