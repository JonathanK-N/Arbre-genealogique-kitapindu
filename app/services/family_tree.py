from __future__ import annotations

from typing import Any, Iterable

from ..constants import PLACEHOLDER_PHOTOS
from ..models import Member


def _member_payload(member: Member) -> dict[str, Any]:
    birth_iso = member.birth_date.isoformat() if member.birth_date else None
    death_iso = member.death_date.isoformat() if member.death_date else None

    initials = "".join(
        filter(
            None,
            [
                member.first_name[:1] if member.first_name else "",
                member.last_name[:1] if member.last_name else "",
            ],
        )
    ).upper()
    if not initials and member.first_name:
        initials = member.first_name[:2].upper()

    return {
        "id": member.id,
        "firstName": member.first_name,
        "lastName": member.last_name,
        "fullName": member.full_name,
        "sex": member.sex or "U",
        "isDeceased": bool(member.is_deceased),
        "birthDate": birth_iso,
        "deathDate": death_iso,
        "address": member.address,
        "notes": member.notes,
        "photo": member.photo_url
        or PLACEHOLDER_PHOTOS.get(member.sex or "U", PLACEHOLDER_PHOTOS["U"]),
        "initials": initials,
    }


def _unit_sort_key(payloads: list[dict[str, Any]]) -> tuple[int, str]:
    def _single_key(payload: dict[str, Any]) -> tuple[int, str]:
        birth = payload.get("birthDate") or "9999-12-31"
        return int(birth.replace("-", "")), payload.get("fullName", "")

    return min((_single_key(p) for p in payloads), default=(99991231, ""))


def _unit_sex(payloads: list[dict[str, Any]]) -> str:
    sexes = {payload.get("sex", "U") for payload in payloads if payload.get("sex")}
    if not sexes:
        return "U"
    if len(sexes) == 1:
        return sexes.pop()
    return "MX"


def _unit_initials(payloads: list[dict[str, Any]]) -> str:
    letters = []
    for payload in payloads:
        first = payload.get("firstName", "")
        if first:
            letters.append(first[0].upper())
    return "".join(letters)[:3]


def build_family_tree(members: Iterable[Member]) -> dict[str, Any]:
    """Group members by union (couple ou célibataire) to construire une hiérarchie stable."""
    members = list(members)
    if not members:
        return {}

    members_map: dict[int, Member] = {member.id: member for member in members}
    family_units: dict[str, dict[str, Any]] = {}
    member_to_unit: dict[int, str] = {}
    processed_couples: set[tuple[int, int]] = set()

    for member in members:
        if member.spouse_id and member.spouse_id in members_map:
            couple_key = tuple(sorted((member.id, member.spouse_id)))
            if couple_key in processed_couples:
                continue
            processed_couples.add(couple_key)

            partner_a = members_map[couple_key[0]]
            partner_b = members_map[couple_key[1]]
            payloads = [_member_payload(partner_a), _member_payload(partner_b)]
            payloads.sort(
                key=lambda payload: (
                    payload.get("birthDate") or "9999-12-31",
                    payload.get("fullName", ""),
                )
            )

            unit_id = f"unit-{couple_key[0]}-{couple_key[1]}"
            unit_sex = _unit_sex(payloads)
            family_units[unit_id] = {
                "unitId": unit_id,
                "label": " & ".join(
                    p.get("firstName", "") for p in payloads if p.get("firstName")
                ),
                "fullLabel": " & ".join(
                    p.get("fullName", "") for p in payloads if p.get("fullName")
                ),
                "members": payloads,
                "sex": unit_sex,
                "initials": _unit_initials(payloads),
                "primaryPhoto": (
                    PLACEHOLDER_PHOTOS["MX"]
                    if unit_sex == "MX"
                    else next((p["photo"] for p in payloads if p.get("photo")), None)
                ),
                "sortKey": _unit_sort_key(payloads),
                "childUnits": set(),
            }
            for payload in payloads:
                member_to_unit[payload["id"]] = unit_id
        else:
            if member.id in member_to_unit:
                continue
            payload = _member_payload(member)
            unit_id = f"unit-{member.id}"
            family_units[unit_id] = {
                "unitId": unit_id,
                "label": payload.get("firstName", payload.get("fullName", "")),
                "fullLabel": payload.get("fullName", payload.get("firstName", "")),
                "members": [payload],
                "sex": _unit_sex([payload]),
                "initials": _unit_initials([payload]),
                "primaryPhoto": payload.get("photo"),
                "sortKey": _unit_sort_key([payload]),
                "childUnits": set(),
            }
            member_to_unit[member.id] = unit_id

    for unit in family_units.values():
        child_units: set[str] = set()
        for payload in unit["members"]:
            member = members_map.get(payload["id"])
            if not member:
                continue
            for child in member.children:
                child_unit = member_to_unit.get(child.id)
                if child_unit and child_unit != unit["unitId"]:
                    child_units.add(child_unit)
        unit["childUnits"] = sorted(
            child_units, key=lambda child_id: family_units[child_id]["sortKey"]
        )

    all_unit_ids = set(family_units.keys())
    referenced_units = {
        child_unit for unit in family_units.values() for child_unit in unit["childUnits"]
    }
    root_units = sorted(
        all_unit_ids - referenced_units,
        key=lambda unit_id: family_units[unit_id]["sortKey"],
    )

    def build_tree(unit_id: str) -> dict[str, Any]:
        unit = family_units[unit_id]
        node = {
            "unitId": unit["unitId"],
            "label": unit["label"],
            "fullLabel": unit["fullLabel"],
            "sex": unit["sex"],
            "initials": unit["initials"],
            "members": unit["members"],
            "primaryPhoto": unit["primaryPhoto"],
            "children": [],
        }
        for child_id in unit["childUnits"]:
            node["children"].append(build_tree(child_id))
        return node

    if len(root_units) == 1:
        return build_tree(root_units[0])

    return {
        "unitId": "kitapindu-root",
        "label": "Famille Kitapindu",
        "fullLabel": "Famille Kitapindu",
        "sex": "U",
        "initials": "FK",
        "members": [],
        "primaryPhoto": None,
        "children": [build_tree(unit_id) for unit_id in root_units],
    }
