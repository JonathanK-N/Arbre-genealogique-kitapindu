from __future__ import annotations

from datetime import date
from typing import Any

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )


class Admin(TimestampMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Admin {self.username}>"


class Member(TimestampMixin, db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column("nom", db.String(120), nullable=False)
    middle_name = db.Column("postnom", db.String(120))
    first_name = db.Column("prenom", db.String(120), nullable=False)
    birth_date = db.Column("date_naissance", db.Date)
    death_date = db.Column("date_deces", db.Date)
    sex = db.Column("sexe", db.String(1), nullable=False)
    address = db.Column("adresse", db.String(255))
    father_id = db.Column("pere_id", db.Integer, db.ForeignKey("members.id"))
    mother_id = db.Column("mere_id", db.Integer, db.ForeignKey("members.id"))
    spouse_id = db.Column("conjoint_id", db.Integer, db.ForeignKey("members.id"))
    photo_url = db.Column("photo", db.String(255))
    notes = db.Column(db.Text)
    is_deceased = db.Column("est_decede", db.Boolean, nullable=False, default=False)

    father = db.relationship(
        "Member",
        remote_side="Member.id",
        foreign_keys=[father_id],
        backref="paternal_children",
    )
    mother = db.relationship(
        "Member",
        remote_side="Member.id",
        foreign_keys=[mother_id],
        backref="maternal_children",
    )
    spouse = db.relationship(
        "Member",
        remote_side="Member.id",
        foreign_keys=[spouse_id],
        post_update=True,
        uselist=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Member {self.full_name}>"

    @property
    def birth_year(self) -> int | None:
        return self.birth_date.year if isinstance(self.birth_date, date) else None

    @property
    def death_year(self) -> int | None:
        return self.death_date.year if isinstance(self.death_date, date) else None

    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def children(self) -> list["Member"]:
        """Merge paternal and maternal links while keeping order predictable."""
        seen = set()
        ordered_children = []
        for child in (*self.paternal_children, *self.maternal_children):
            if child.id not in seen:
                ordered_children.append(child)
                seen.add(child.id)
        return ordered_children

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nom": self.last_name,
            "postnom": self.middle_name,
            "prenom": self.first_name,
            "date_naissance": self.birth_date.isoformat()
            if isinstance(self.birth_date, date)
            else None,
            "date_deces": self.death_date.isoformat()
            if isinstance(self.death_date, date)
            else None,
            "sexe": self.sex,
            "adresse": self.address,
            "pere_id": self.father_id,
            "mere_id": self.mother_id,
            "conjoint_id": self.spouse_id,
            "photo": self.photo_url,
            "notes": self.notes,
            "est_decede": self.is_deceased,
        }

    def to_tree_node(self) -> dict[str, Any]:
        """Shape the member data for D3 tree consumption."""
        payload: dict[str, Any] = {
            "id": self.id,
            "fullName": self.full_name,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "sex": self.sex,
            "isDeceased": bool(self.is_deceased),
            "birthDate": self.birth_date.isoformat()
            if isinstance(self.birth_date, date)
            else None,
            "deathDate": self.death_date.isoformat()
            if isinstance(self.death_date, date)
            else None,
            "address": self.address,
            "notes": self.notes,
            "photo": self.photo_url,
        }

        if self.spouse:
            payload["spouse"] = {
                "id": self.spouse.id,
                "fullName": self.spouse.full_name,
                "firstName": self.spouse.first_name,
                "lastName": self.spouse.last_name,
                "sex": self.spouse.sex,
                "isDeceased": bool(self.spouse.is_deceased),
                "birthDate": self.spouse.birth_date.isoformat()
                if isinstance(self.spouse.birth_date, date)
                else None,
                "deathDate": self.spouse.death_date.isoformat()
                if isinstance(self.spouse.death_date, date)
                else None,
            }

        if self.children:
            payload["children"] = [child.id for child in self.children]

        return payload
