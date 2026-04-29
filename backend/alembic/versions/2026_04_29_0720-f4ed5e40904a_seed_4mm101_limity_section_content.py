"""seed 4MM101 limity section content

Revision ID: f4ed5e40904a
Revises: 5d9486ef38a3
Create Date: 2026-04-29 07:20:13.966842

Pure-data migration: inserts the "Limity funkce" section into the
4MM101 course, four lessons, and ten exercises. Idempotent via
ON CONFLICT DO NOTHING on the composite (parent_id, order_index)
unique constraints — re-running the migration is a no-op.

Decoupled from the application's ORM models: schema is described
inline via sa.table() so future model renames don't break this
historical migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert as pg_insert


# revision identifiers, used by Alembic.
revision: str = 'f4ed5e40904a'
down_revision: Union[str, Sequence[str], None] = '5d9486ef38a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------- Inline schema (decoupled from ORM models) ----------

courses = sa.table(
    "courses",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("code", sa.String),
)

sections = sa.table(
    "sections",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("course_id", UUID(as_uuid=True)),
    sa.column("order_index", sa.Integer),
    sa.column("title", sa.String),
    sa.column("description", sa.Text),
)

lessons = sa.table(
    "lessons",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("section_id", UUID(as_uuid=True)),
    sa.column("order_index", sa.Integer),
    sa.column("title", sa.String),
    sa.column("description", sa.Text),
    sa.column("xp_reward", sa.Integer),
)

exercises = sa.table(
    "exercises",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("lesson_id", UUID(as_uuid=True)),
    sa.column("order_index", sa.Integer),
    sa.column("exercise_type", sa.String),
    sa.column("prompt", sa.Text),
    sa.column("explanation", sa.Text),
    sa.column("difficulty", sa.Integer),
    sa.column("payload", JSONB),
)


# ---------- Content data ----------

SECTION = {
    "order_index": 1,
    "title": "Limity funkce",
    "description": (
        "Úvod do pojmu limita funkce v bodě, jednostranné limity "
        "a základní pravidla pro výpočet limit."
    ),
}

LESSONS = [
    {
        "order_index": 1,
        "title": "Pojem limity",
        "description": "Co znamená \"limita funkce v bodě\" intuitivně i formálně.",
        "xp_reward": 10,
    },
    {
        "order_index": 2,
        "title": "Limity v nevlastních bodech",
        "description": "Limity v nekonečnu a v bodech, kde funkce není definována.",
        "xp_reward": 15,
    },
    {
        "order_index": 3,
        "title": "Jednostranné limity",
        "description": "Limity zleva a zprava, vztah k oboustranné limitě.",
        "xp_reward": 15,
    },
    {
        "order_index": 4,
        "title": "Pravidla pro výpočet limit",
        "description": "Aritmetika limit, neurčité výrazy a základní techniky.",
        "xp_reward": 20,
    },
]

# exercises grouped by lesson order_index → list[dict]
EXERCISES = {
    1: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 1,
            "prompt": "Co intuitivně znamená zápis $\\lim_{x \\to 2} f(x) = 5$?",
            "explanation": (
                "Limita popisuje chování funkce v okolí bodu, ne nutně v bodě "
                "samém. Funkce nemusí být v bodě 2 vůbec definovaná, přesto "
                "limita může existovat."
            ),
            "payload": {
                "options": [
                    "Funkce f(x) má v bodě x = 2 hodnotu 5.",
                    "Když se x blíží k 2, hodnoty f(x) se blíží k 5.",
                    "Funkce f(x) je rovna 5 pro všechna x.",
                    "Funkce f(x) má v bodě 5 hodnotu 2.",
                ],
                "correct_index": 1,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": "Která z následujících tvrzení o limitě je správné?",
            "explanation": (
                "Limita, pokud existuje, je vždy jednoznačná. Nemusí ale "
                "existovat (např. u skokových funkcí) a nemusí se shodovat "
                "s funkční hodnotou."
            ),
            "payload": {
                "options": [
                    "Limita funkce v bodě vždy existuje.",
                    "Pokud limita existuje, je jednoznačně určena.",
                    "Limita je vždy rovna funkční hodnotě v daném bodě.",
                    "Limita může mít více různých hodnot současně.",
                ],
                "correct_index": 1,
            },
        },
        {
            "order_index": 3,
            "exercise_type": "numeric",
            "difficulty": 1,
            "prompt": "Spočítej $\\lim_{x \\to 3} (x + 4)$.",
            "explanation": (
                "Pro spojité funkce platí $\\lim_{x \\to a} f(x) = f(a)$. "
                "Tedy $\\lim_{x \\to 3} (x + 4) = 3 + 4 = 7$."
            ),
            "payload": {"expected": 7, "tolerance": 0.001},
        },
    ],
    2: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": "Čemu se rovná $\\lim_{x \\to \\infty} \\frac{1}{x}$?",
            "explanation": (
                "Když x roste do nekonečna, hodnota $\\frac{1}{x}$ se blíží "
                "nule. Tedy limita je 0."
            ),
            "payload": {
                "options": ["0", "1", "$\\infty$", "Limita neexistuje."],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "numeric",
            "difficulty": 3,
            "prompt": "Spočítej $\\lim_{x \\to \\infty} \\frac{2x + 1}{x}$.",
            "explanation": (
                "Vydělíme čitatele i jmenovatele nejvyšší mocninou: "
                "$\\frac{2x + 1}{x} = 2 + \\frac{1}{x}$. V nekonečnu je "
                "$\\frac{1}{x} \\to 0$, tedy limita je 2."
            ),
            "payload": {"expected": 2, "tolerance": 0.001},
        },
    ],
    3: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "Pokud $\\lim_{x \\to a^-} f(x) = 3$ a "
                "$\\lim_{x \\to a^+} f(x) = 5$, co lze říct "
                "o $\\lim_{x \\to a} f(x)$?"
            ),
            "explanation": (
                "Oboustranná limita existuje pouze tehdy, pokud se obě "
                "jednostranné limity rovnají. V tomto případě 3 ≠ 5, tedy "
                "limita neexistuje."
            ),
            "payload": {
                "options": [
                    "Limita je rovna 4 (průměr).",
                    "Limita neexistuje.",
                    "Limita je rovna 3.",
                    "Limita je rovna 5.",
                ],
                "correct_index": 1,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "multiple_choice",
            "difficulty": 3,
            "prompt": "Čemu se rovná $\\lim_{x \\to 0^+} \\frac{1}{x}$?",
            "explanation": (
                "Když se x blíží k nule zprava (kladnými hodnotami), "
                "$\\frac{1}{x}$ roste neomezeně. Tedy limita je $+\\infty$."
            ),
            "payload": {
                "options": [
                    "0",
                    "$+\\infty$",
                    "$-\\infty$",
                    "Limita neexistuje.",
                ],
                "correct_index": 1,
            },
        },
    ],
    4: [
        {
            "order_index": 1,
            "exercise_type": "numeric",
            "difficulty": 2,
            "prompt": "Spočítej $\\lim_{x \\to 2} (x^2 - 3x + 1)$.",
            "explanation": (
                "Polynom je spojitý, tedy "
                "$\\lim_{x \\to 2} (x^2 - 3x + 1) = 4 - 6 + 1 = -1$."
            ),
            "payload": {"expected": -1, "tolerance": 0.001},
        },
        {
            "order_index": 2,
            "exercise_type": "multiple_choice",
            "difficulty": 3,
            "prompt": "Která z následujících je neurčitý výraz?",
            "explanation": (
                "Tvar $\\frac{0}{0}$ je neurčitý — výsledek závisí na "
                "konkrétních funkcích. Ostatní tvary jsou určité (postupně "
                "0, ±∞ a ±∞)."
            ),
            "payload": {
                "options": [
                    "$\\frac{0}{1}$",
                    "$\\frac{0}{0}$",
                    "$\\frac{\\infty}{1}$",
                    "$\\frac{1}{0}$",
                ],
                "correct_index": 1,
            },
        },
        {
            "order_index": 3,
            "exercise_type": "numeric",
            "difficulty": 4,
            "prompt": "Spočítej $\\lim_{x \\to 1} \\frac{x^2 - 1}{x - 1}$.",
            "explanation": (
                "Výraz vede na $\\frac{0}{0}$ (neurčitý tvar). Faktorizujeme: "
                "$\\frac{x^2 - 1}{x - 1} = \\frac{(x-1)(x+1)}{x-1} = x + 1$. "
                "Limita je $1 + 1 = 2$."
            ),
            "payload": {"expected": 2, "tolerance": 0.001},
        },
    ],
}


# ---------- Helpers ----------

def _upsert_returning_id(bind, table, conflict_cols, lookup_cond, **values):
    """Insert with ON CONFLICT DO NOTHING; if a row is returned, return its id;
    otherwise the row already existed — fall back to a SELECT for its id.
    """
    stmt = (
        pg_insert(table)
        .values(**values)
        .on_conflict_do_nothing(index_elements=conflict_cols)
        .returning(table.c.id)
    )
    row = bind.execute(stmt).first()
    if row is not None:
        return row[0]
    return bind.execute(sa.select(table.c.id).where(lookup_cond)).scalar_one()


# ---------- Migration ----------

def upgrade() -> None:
    bind = op.get_bind()

    course_id = bind.execute(
        sa.select(courses.c.id).where(courses.c.code == "4MM101")
    ).scalar_one()

    section_id = _upsert_returning_id(
        bind,
        sections,
        conflict_cols=["course_id", "order_index"],
        lookup_cond=sa.and_(
            sections.c.course_id == course_id,
            sections.c.order_index == SECTION["order_index"],
        ),
        course_id=course_id,
        order_index=SECTION["order_index"],
        title=SECTION["title"],
        description=SECTION["description"],
    )

    for lesson in LESSONS:
        lesson_id = _upsert_returning_id(
            bind,
            lessons,
            conflict_cols=["section_id", "order_index"],
            lookup_cond=sa.and_(
                lessons.c.section_id == section_id,
                lessons.c.order_index == lesson["order_index"],
            ),
            section_id=section_id,
            order_index=lesson["order_index"],
            title=lesson["title"],
            description=lesson["description"],
            xp_reward=lesson["xp_reward"],
        )

        for exercise in EXERCISES[lesson["order_index"]]:
            _upsert_returning_id(
                bind,
                exercises,
                conflict_cols=["lesson_id", "order_index"],
                lookup_cond=sa.and_(
                    exercises.c.lesson_id == lesson_id,
                    exercises.c.order_index == exercise["order_index"],
                ),
                lesson_id=lesson_id,
                order_index=exercise["order_index"],
                exercise_type=exercise["exercise_type"],
                prompt=exercise["prompt"],
                explanation=exercise["explanation"],
                difficulty=exercise["difficulty"],
                payload=exercise["payload"],
            )


def downgrade() -> None:
    bind = op.get_bind()

    course_id = bind.execute(
        sa.select(courses.c.id).where(courses.c.code == "4MM101")
    ).scalar_one_or_none()
    if course_id is None:
        return

    section_id = bind.execute(
        sa.select(sections.c.id).where(
            sections.c.course_id == course_id,
            sections.c.order_index == SECTION["order_index"],
        )
    ).scalar_one_or_none()
    if section_id is None:
        return

    # FK ondelete=CASCADE handles lessons and exercises automatically;
    # deleting the section sweeps the whole subtree.
    bind.execute(sa.delete(sections).where(sections.c.id == section_id))
