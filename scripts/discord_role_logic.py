"""Role add/remove rules for reaction roles (IDs, no discord.py import)."""
from __future__ import annotations

from discord_role_catalog import GROUP_META, ROLE_GROUPS


def plan_role_change_ids(
    member_group_ids: list[int],
    group_role_ids: set[int],
    target_id: int,
    group: str,
    role_name: str,
    max_v: int,
) -> dict:
    if target_id not in group_role_ids:
        return {"message": "Unknown role."}

    current = [rid for rid in member_group_ids if rid in group_role_ids]
    has = target_id in current
    to_remove: list[int] = []
    to_add: list[int] = []

    if max_v == 1:
        if has:
            return {"message": f"You already have **{role_name}**."}
        to_remove = list(current)
        to_add = [target_id]
    elif has:
        to_remove = [target_id]
    elif group == "exam" and role_name == "No Exam Yet":
        to_remove = list(current)
        to_add = [target_id]
    elif group == "exam":
        # caller passes role names via role_name; strip No Exam Yet by count
        if len(current) >= max_v:
            to_remove.append(current[0])
        to_add = [target_id]
    else:
        if len(current) >= max_v:
            to_remove.append(current[0])
        to_add = [target_id]

    return {"remove": to_remove, "add": to_add}
