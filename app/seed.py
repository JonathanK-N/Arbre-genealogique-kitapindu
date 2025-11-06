from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from itertools import cycle, count
from typing import Any

from werkzeug.security import generate_password_hash

from .constants import PLACEHOLDER_PHOTOS
from .extensions import db
from .models import Admin, Member


def _parse_date(value: str | None) -> datetime.date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _photo_fallback(sex: str | None) -> str:
    return PLACEHOLDER_PHOTOS.get(sex or "U", PLACEHOLDER_PHOTOS["U"])


def build_seed_members() -> list[dict[str, Any]]:
    male_names = cycle(
        [
            "Jean",
            "Paul",
            "David",
            "Samuel",
            "André",
            "Joseph",
            "Louis",
            "François",
            "Gabriel",
            "Raphaël",
            "Daniel",
            "Simon",
            "Pierre",
            "Claude",
            "Patrick",
            "Marcel",
            "Félix",
            "Luc",
            "Thierry",
            "Benoît",
            "Grégoire",
            "Damien",
            "Noël",
            "Bruno",
            "Oscar",
            "Sylvain",
            "Roger",
            "Armand",
            "Jason",
        ]
    )
    female_names = cycle(
        [
            "Sophie",
            "Claire",
            "Ruth",
            "Esther",
            "Laetitia",
            "Pauline",
            "Aline",
            "Chantal",
            "Mélissa",
            "Nathalie",
            "Julienne",
            "Isabelle",
            "Madeleine",
            "Patricia",
            "Monique",
            "Sandrine",
            "Jacqueline",
            "Clarisse",
            "Inès",
            "Aurélie",
            "Josiane",
            "Olivia",
            "Agathe",
            "Annie",
            "Delphine",
            "Amanda",
            "Justine",
            "Sylvie",
            "Carole",
        ]
    )
    spouse_last_names = cycle(
        [
            "Masengo",
            "Mutombo",
            "Tshibanda",
            "Kasongo",
            "Kalema",
            "Ngoyi",
            "Mununga",
            "Kasindi",
            "Mboyo",
            "Kabasele",
            "Beya",
            "Mwila",
            "Kabeya",
            "Kalombo",
            "Ilunga",
            "Kayembe",
            "Mukeba",
            "Mulongo",
            "Tshiani",
            "Mubayi",
            "Dibwe",
            "Banza",
            "Mpoyi",
            "Nkoy",
            "Kabamba",
            "Likuta",
            "Tshomba",
            "Mbula",
            "Mundele",
            "Ngoma",
        ]
    )
    address_pool = cycle(
        [
            "Kinshasa, Gombe",
            "Kinshasa, Limete",
            "Kinshasa, Bandalungwa",
            "Kinshasa, Kasa-Vubu",
            "Lubumbashi, Golf",
            "Lubumbashi, Kenya",
            "Mbuji-Mayi, Dibindi",
            "Kananga, Katoka",
            "Goma, Karisimbi",
            "Bukavu, Kadutu",
            "Matadi, Nzanza",
            "Kisangani, Makiso",
            "Mbandaka, Botawa",
            "Kolwezi, Dilala",
            "Boma, Kalamu",
        ]
    )

    slug_counts: dict[str, int] = defaultdict(int)
    members: list[dict[str, Any]] = []
    code_map: dict[str, dict[str, Any]] = {}
    birth_counter = count(1)

    def next_birth_date(year: int) -> str:
        idx = next(birth_counter)
        month = (idx % 12) + 1
        day = (idx % 27) + 1
        return f"{year:04d}-{month:02d}-{day:02d}"

    def make_code(first_name: str, last_name: str, preferred: str | None = None) -> str:
        if preferred:
            slug = preferred
        else:
            slug = f"{first_name.lower()}_{last_name.lower()}".replace(" ", "_").replace("'", "")
        slug_counts[slug] += 1
        if slug_counts[slug] == 1:
            return slug
        return f"{slug}_{slug_counts[slug]}"

    def add_member(
        first_name: str,
        last_name: str,
        sex: str,
        birth_year: int,
        address: str,
        *,
        middle_name: str | None = None,
        father: str | None = None,
        mother: str | None = None,
        code: str | None = None,
        notes: str | None = None,
        is_deceased: bool | None = None,
    ) -> str:
        assigned_code = make_code(first_name, last_name, preferred=code)
        birth = next_birth_date(birth_year)
        if is_deceased is None:
            is_deceased = birth_year <= 1955
        member = {
            "code": assigned_code,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "sex": sex,
            "birth": birth,
            "address": address,
            "father": father,
            "mother": mother,
            "spouse": None,
            "notes": notes,
            "is_deceased": is_deceased,
        }
        members.append(member)
        code_map[assigned_code] = member
        return assigned_code

    def link_spouses(code_a: str, code_b: str) -> None:
        code_map[code_a]["spouse"] = code_b
        code_map[code_b]["spouse"] = code_a

    # Generation 1 – fondateurs
    founder_father = add_member(
        "Mwamba",
        "Kitapindu",
        "M",
        1920,
        "Kinshasa, Lemba",
        code="mwamba_kitapindu",
        is_deceased=True,
    )
    founder_mother = add_member(
        "Marie",
        "Mbuyi",
        "F",
        1925,
        "Kinshasa, Lemba",
        code="marie_mbuyi",
        is_deceased=True,
    )
    link_spouses(founder_father, founder_mother)

    families: list[dict[str, Any]] = [
        {
            "father": founder_father,
            "mother": founder_mother,
            "child_last_name": "Kitapindu",
            "child_start_year": 1948,
            "address": "Kinshasa, Kasa-Vubu",
        }
    ]

    children_plan = [4, 3, 2, 2, 1]  # generations 2 -> 6
    next_generation_caps = [None, 12, 20, 28, 0]

    for generation_number, children_per_family in enumerate(children_plan, start=2):
        new_families: list[dict[str, Any]] = []
        cap_index = generation_number - 2
        next_cap = (
            next_generation_caps[cap_index]
            if 0 <= cap_index < len(next_generation_caps)
            else None
        )
        is_last_generation = generation_number == 6

        for family_index, family in enumerate(families):
            for child_order in range(children_per_family):
                sex = "M" if (child_order + family_index) % 2 == 0 else "F"
                first_name = next(male_names) if sex == "M" else next(female_names)
                last_name = family["child_last_name"]
                birth_year = family["child_start_year"] + child_order * 2
                child_code = add_member(
                    first_name,
                    last_name,
                    sex,
                    birth_year,
                    family["address"],
                    father=family["father"],
                    mother=family["mother"],
                    is_deceased=birth_year <= 1965,
                )

                if is_last_generation:
                    continue

                spouse_sex = "F" if sex == "M" else "M"
                spouse_first = next(female_names) if spouse_sex == "F" else next(male_names)
                spouse_last = next(spouse_last_names)
                spouse_birth_year = birth_year + (2 if spouse_sex == "F" else -2)
                spouse_address = next(address_pool)
                spouse_code = add_member(
                    spouse_first,
                    spouse_last,
                    spouse_sex,
                    spouse_birth_year,
                    spouse_address,
                    is_deceased=False,
                )
                link_spouses(child_code, spouse_code)

                if generation_number < 6:
                    if sex == "M":
                        child_last_name = last_name
                        father_code = child_code
                        mother_code = spouse_code
                    else:
                        child_last_name = spouse_last
                        father_code = spouse_code
                        mother_code = child_code

                    if next_cap is None or len(new_families) < next_cap:
                        new_families.append(
                            {
                                "father": father_code,
                                "mother": mother_code,
                                "child_last_name": child_last_name,
                                "child_start_year": birth_year + 24,
                                "address": spouse_address,
                            }
                        )

        families = new_families
        if not families:
            break

    if len(members) < 150:
        raise ValueError(
            f"Seed dataset too small ({len(members)} entries). Increase generation parameters."
        )

    return members


SEED_MEMBERS = build_seed_members()


def ensure_seed_data() -> None:
    """Populate the database with default admin credentials and sample tree data."""
    if Admin.query.count() == 0:
        admin = Admin(
            username="admin",
            password_hash=generate_password_hash("kitapindu2024"),
        )
        db.session.add(admin)
        db.session.commit()

    if Member.query.count() > 0:
        return

    code_index: dict[str, Member] = {}

    for entry in SEED_MEMBERS:
        member = Member(
            first_name=entry["first_name"],
            middle_name=entry.get("middle_name"),
            last_name=entry["last_name"],
            sex=entry["sex"],
            birth_date=_parse_date(entry.get("birth")),
            death_date=_parse_date(entry.get("death")),
            address=entry.get("address"),
            notes=entry.get("notes"),
            is_deceased=bool(entry.get("is_deceased", False)),
            photo_url=entry.get("photo") or _photo_fallback(entry.get("sex")),
        )
        db.session.add(member)
        db.session.flush()
        code_index[entry["code"]] = member

    for entry in SEED_MEMBERS:
        member = code_index[entry["code"]]
        father_code = entry.get("father")
        mother_code = entry.get("mother")
        spouse_code = entry.get("spouse")

        if father_code:
            member.father = code_index.get(father_code)
        if mother_code:
            member.mother = code_index.get(mother_code)
        if spouse_code:
            spouse = code_index.get(spouse_code)
            if spouse:
                member.spouse = spouse
                if spouse.spouse is None:
                    spouse.spouse = member

    db.session.commit()
