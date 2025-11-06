from collections import defaultdict, deque
from typing import Any, Callable

from flask import Blueprint, abort, render_template

from ..models import Member

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def index():
    return render_template("index.html")


def _compute_generation_levels(members: list[Member]) -> dict[int, int]:
    members_by_id = {m.id: m for m in members}
    children = defaultdict(list)
    potential_roots = set(members_by_id.keys())

    for member in members:
        if member.father_id:
            children[member.father_id].append(member.id)
            potential_roots.discard(member.id)
        if member.mother_id:
            children[member.mother_id].append(member.id)
            potential_roots.discard(member.id)

    if not potential_roots:
        potential_roots = {
            m.id for m in members if not m.father_id and not m.mother_id
        } or set(members_by_id.keys())

    levels: dict[int, int] = {}
    queue: deque[tuple[int, int]] = deque((root_id, 1) for root_id in potential_roots)

    while queue:
        current_id, level = queue.popleft()
        if current_id in levels:
            continue
        levels[current_id] = level
        for child_id in children.get(current_id, []):
            queue.append((child_id, level + 1))

    changed = True
    while changed:
        changed = False
        for member in members:
            if member.id in levels:
                continue
            if member.spouse_id and member.spouse_id in levels:
                levels[member.id] = levels[member.spouse_id]
                changed = True

    for member in members:
        levels.setdefault(member.id, 1)

    return levels


@public_bp.get("/analytics/<string:view>")
def analytics_detail(view: str):
    members = Member.query.order_by(Member.birth_date.asc().nullslast()).all()
    if not members:
        return render_template(
            "analytics_detail.html",
            title="Analyse généalogique",
            description="Aucune donnée disponible pour le moment.",
            sections=[],
            detail_cards=[],
        )

    view_map: dict[str, dict[str, Any]] = {
        "members": {
            "title": "Tous les membres recensés",
            "description": "Liste exhaustive des personnes enregistrées, classées par génération.",
            "filter": lambda m: True,
        },
        "male-lines": {
            "title": "Lignées masculines",
            "description": "Branches issues des descendants Kitapindu par la ligne paternelle.",
            "filter": lambda m: m.sex == "M",
        },
        "female-lines": {
            "title": "Lignées féminines",
            "description": "Branches portées par les filles Kitapindu et leurs alliances.",
            "filter": lambda m: m.sex == "F",
        },
        "living": {
            "title": "Membres vivants",
            "description": "Les membres actuellement recensés comme vivants.",
            "filter": lambda m: not m.is_deceased,
        },
        "deceased": {
            "title": "Membres décédés",
            "description": "Les membres reconnus comme disparus.",
            "filter": lambda m: m.is_deceased,
        },
        "depth": {
            "title": "Répartition par générations",
            "description": "Effectifs par génération, ainsi que la proportion masculine/féminine et le statut vie/décès.",
            "filter": None,
        },
    }

    config = view_map.get(view)
    if not config:
        abort(404)

    generation_levels = _compute_generation_levels(members)
    max_generation = max(generation_levels.values(), default=1)
    members_by_generation = defaultdict(list)
    for member in members:
        members_by_generation[generation_levels[member.id]].append(member)

    detail_cards = [
        {
            "label": "Total membres",
            "value": len(members),
        },
        {
            "label": "Lignées masculines",
            "value": sum(1 for m in members if m.sex == "M"),
        },
        {
            "label": "Lignées féminines",
            "value": sum(1 for m in members if m.sex == "F"),
        },
        {
            "label": "Générations couvertes",
            "value": max_generation,
        },
    ]

    sections: list[dict[str, Any]] = []

    if view == "depth":
        for generation in range(1, max_generation + 1):
            generation_members = members_by_generation.get(generation, [])
            if not generation_members:
                continue
            sections.append(
                {
                    "generation": generation,
                    "summary": {
                        "total": len(generation_members),
                        "male": sum(1 for m in generation_members if m.sex == "M"),
                        "female": sum(1 for m in generation_members if m.sex == "F"),
                        "living": sum(1 for m in generation_members if not m.is_deceased),
                        "deceased": sum(
                            1 for m in generation_members if m.is_deceased
                        ),
                    },
                }
            )
    else:
        filter_fn: Callable[[Member], bool] = config["filter"]
        filtered_total = sum(1 for m in members if filter_fn(m))
        detail_cards.append(
            {
                "label": "Total filtré",
                "value": filtered_total,
            }
        )
        for generation in range(1, max_generation + 1):
            generation_members = [
                member
                for member in members_by_generation.get(generation, [])
                if filter_fn(member)
            ]
            if not generation_members:
                continue
            sections.append(
                {
                    "generation": generation,
                    "members": generation_members,
                }
            )

    return render_template(
        "analytics_detail.html",
        title=config["title"],
        description=config["description"],
        sections=sections,
        detail_cards=detail_cards,
        view=view,
    )
