"""clarify E4.4 (Bolzano matching) explanation re 1/x sign condition

Revision ID: b2d3e4f5a6c7
Revises: a1c2d3e4f5b6
Create Date: 2026-05-05 13:20:00.000000

For $f(x) = 1/x$ on $\\langle -1, 1 \\rangle$ the sign condition
($f(-1) \\cdot f(1) = -1 < 0$) is actually satisfied — the theorem
fails because of the discontinuity at 0, not because of the signs.
The original explanation glossed over this and a careful student
could plausibly land on the right answer for the wrong reason.
Append a Pozor: line that names the actual reason.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "b2d3e4f5a6c7"
down_revision: Union[str, Sequence[str], None] = "a1c2d3e4f5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
)
lessons = sa.table(
    "lessons",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("section_id", UUID(as_uuid=True)),
    sa.column("order_index", sa.Integer),
)
exercises = sa.table(
    "exercises",
    sa.column("id", UUID(as_uuid=True)),
    sa.column("lesson_id", UUID(as_uuid=True)),
    sa.column("order_index", sa.Integer),
    sa.column("explanation", sa.Text),
)


OLD_EXPLANATION = (
    "Předpoklady jsou dva: spojitost na uzavřeném intervalu a "
    "opačná znaménka v krajních bodech. Stačí jeden předpoklad "
    "porušit a věta neplatí."
)

NEW_EXPLANATION = (
    "Předpoklady jsou dva: spojitost na uzavřeném intervalu a "
    "opačná znaménka v krajních bodech. Stačí jeden předpoklad "
    "porušit a věta neplatí. Pozor: u $\\frac{1}{x}$ jsou znaménka "
    "v krajních bodech opačná ($f(-1) \\cdot f(1) = -1 < 0$), ale "
    "věta neplatí kvůli nespojitosti v 0."
)


def _e4_4_id(bind):
    """Find the exercise UUID for section 1 → lesson 4 → exercise 4 of 4MM101."""
    return bind.execute(
        sa.select(exercises.c.id)
        .select_from(
            exercises.join(lessons, lessons.c.id == exercises.c.lesson_id)
            .join(sections, sections.c.id == lessons.c.section_id)
            .join(courses, courses.c.id == sections.c.course_id)
        )
        .where(
            courses.c.code == "4MM101",
            sections.c.order_index == 1,
            lessons.c.order_index == 4,
            exercises.c.order_index == 4,
        )
    ).scalar_one_or_none()


def upgrade() -> None:
    bind = op.get_bind()
    ex_id = _e4_4_id(bind)
    if ex_id is None:
        return  # seed not present yet — nothing to update
    bind.execute(
        sa.update(exercises)
        .where(exercises.c.id == ex_id)
        .values(explanation=NEW_EXPLANATION)
    )


def downgrade() -> None:
    bind = op.get_bind()
    ex_id = _e4_4_id(bind)
    if ex_id is None:
        return
    bind.execute(
        sa.update(exercises)
        .where(exercises.c.id == ex_id)
        .values(explanation=OLD_EXPLANATION)
    )
