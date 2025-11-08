from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..extensions import db
from ..models import Member
from ..services.family_tree import build_family_tree
from ..utils.auth import admin_login_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _parse_date(value: str | None) -> datetime.date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _serialize_member(member: Member) -> dict[str, Any]:
    payload = member.to_dict()
    payload["full_name"] = member.full_name
    payload["children_ids"] = [child.id for child in member.children]
    if member.spouse:
        payload["spouse"] = {
            "id": member.spouse.id,
            "full_name": member.spouse.full_name,
        }
    else:
        payload["spouse"] = None
    return payload


def _apply_relationships(member: Member, data: dict[str, Any]) -> None:
    father_id = data.get("pere_id")
    mother_id = data.get("mere_id")
    spouse_id = data.get("conjoint_id")

    member.father = Member.query.get(father_id) if father_id else None
    member.mother = Member.query.get(mother_id) if mother_id else None

    spouse = Member.query.get(spouse_id) if spouse_id else None
    if spouse and spouse.id != member.id:
        member.spouse = spouse
        if spouse.spouse_id != member.id:
            spouse.spouse = member
    else:
        if member.spouse and member.spouse.spouse_id == member.id:
            member.spouse.spouse = None
        member.spouse = None


def _hydrate_member(member: Member, data: dict[str, Any]) -> Member:
    member.last_name = data.get("nom", member.last_name)
    member.middle_name = data.get("postnom")
    member.first_name = data.get("prenom", member.first_name)
    member.sex = data.get("sexe", member.sex)
    member.address = data.get("adresse")
    member.photo_url = data.get("photo")
    member.notes = data.get("notes")
    member.is_deceased = bool(data.get("est_decede", False))
    member.birth_date = _parse_date(data.get("date_naissance"))
    member.death_date = _parse_date(data.get("date_deces"))

    _apply_relationships(member, data)
    return member


@api_bp.get("/v1/members")
def list_members():
    search = request.args.get("search", "").strip()
    query = Member.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Member.first_name.ilike(search_pattern),
                Member.middle_name.ilike(search_pattern),
                Member.last_name.ilike(search_pattern),
            )
        )

    order = request.args.get("order", "asc")
    if order == "desc":
        query = query.order_by(Member.birth_date.desc().nullslast())
    else:
        query = query.order_by(Member.birth_date.asc().nullslast())

    members = query.all()
    return jsonify([_serialize_member(member) for member in members])


@api_bp.get("/v1/members/<int:member_id>")
def get_member(member_id: int):
    member = Member.query.get_or_404(member_id)
    return jsonify(_serialize_member(member))


@api_bp.post("/v1/members")
@admin_login_required
def create_member():
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"error": "Payload JSON invalide"}), HTTPStatus.BAD_REQUEST

    member = _hydrate_member(Member(), payload)
    db.session.add(member)
    db.session.commit()
    return jsonify(_serialize_member(member)), HTTPStatus.CREATED


@api_bp.put("/v1/members/<int:member_id>")
@admin_login_required
def update_member(member_id: int):
    member = Member.query.get_or_404(member_id)
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({"error": "Payload JSON invalide"}), HTTPStatus.BAD_REQUEST

    _hydrate_member(member, payload)
    db.session.commit()
    return jsonify(_serialize_member(member))


@api_bp.delete("/v1/members/<int:member_id>")
@admin_login_required
def delete_member(member_id: int):
    member = Member.query.get_or_404(member_id)

    for child in member.children:
        if child.father_id == member.id:
            child.father = None
        if child.mother_id == member.id:
            child.mother = None

    if member.spouse and member.spouse.spouse_id == member.id:
        member.spouse.spouse = None

    db.session.delete(member)
    db.session.commit()
    return "", HTTPStatus.NO_CONTENT


@api_bp.get("/v1/tree")
def family_tree():
    members = Member.query.order_by(Member.birth_date.asc().nullslast()).all()
    tree = build_family_tree(members)
    return jsonify(tree)


# Backward compatibility with the initial MVP routes
@api_bp.get("/membres")
def legacy_members():
    return list_members()


@api_bp.post("/membres")
@admin_login_required
def legacy_create_member():
    return create_member()
