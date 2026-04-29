"""extend exercise_attempts for granular tracking

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-29 14:45:00.000000

Extends exercise_attempts with denormalised columns (user_id, exercise_type,
section_id, lesson_id) so per-section / per-type stats can be computed
without joining four tables on every aggregation. Also makes time_spent_ms
nullable — frontend doesn't send per-exercise timings yet, the column
becomes opt-in for future instrumentation.

Strategy:
1. Add new columns as nullable.
2. Back-fill via JOIN through lesson_attempts → lessons + exercises.
3. ALTER ... SET NOT NULL on the four denormalised columns.
4. Drop NOT NULL on time_spent_ms.
5. Add three composite indexes for the per-user aggregations the stats
   endpoint runs.

The table is empty in production (the submit handler never inserted
into it), so the back-fill is a no-op; for local DBs that did exercise
attempts via earlier flows the JOIN populates the columns deterministically.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercise_attempts",
        sa.Column("user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "exercise_attempts",
        sa.Column("exercise_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "exercise_attempts",
        sa.Column("section_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "exercise_attempts",
        sa.Column("lesson_id", sa.UUID(), nullable=True),
    )

    # Postgres UPDATE...FROM can't re-reference the target table in the
    # FROM clause, so the source tables are listed comma-style and the
    # joins to the target row happen entirely in WHERE.
    op.execute(
        """
        UPDATE exercise_attempts ea
        SET
            user_id = la.user_id,
            lesson_id = la.lesson_id,
            section_id = l.section_id,
            exercise_type = e.exercise_type
        FROM lesson_attempts la, lessons l, exercises e
        WHERE ea.lesson_attempt_id = la.id
          AND l.id = la.lesson_id
          AND e.id = ea.exercise_id
        """
    )

    op.alter_column("exercise_attempts", "user_id", nullable=False)
    op.alter_column("exercise_attempts", "exercise_type", nullable=False)
    op.alter_column("exercise_attempts", "section_id", nullable=False)
    op.alter_column("exercise_attempts", "lesson_id", nullable=False)

    op.alter_column("exercise_attempts", "time_spent_ms", nullable=True)

    op.create_foreign_key(
        "fk_exercise_attempts_user_id",
        "exercise_attempts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_exercise_attempts_section_id",
        "exercise_attempts",
        "sections",
        ["section_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_exercise_attempts_lesson_id",
        "exercise_attempts",
        "lessons",
        ["lesson_id"],
        ["id"],
    )

    op.create_index(
        "ix_exercise_attempts_user_created",
        "exercise_attempts",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_exercise_attempts_user_section",
        "exercise_attempts",
        ["user_id", "section_id"],
    )
    op.create_index(
        "ix_exercise_attempts_user_type",
        "exercise_attempts",
        ["user_id", "exercise_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_exercise_attempts_user_type", table_name="exercise_attempts"
    )
    op.drop_index(
        "ix_exercise_attempts_user_section", table_name="exercise_attempts"
    )
    op.drop_index(
        "ix_exercise_attempts_user_created", table_name="exercise_attempts"
    )
    op.drop_constraint(
        "fk_exercise_attempts_lesson_id", "exercise_attempts", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_exercise_attempts_section_id", "exercise_attempts", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_exercise_attempts_user_id", "exercise_attempts", type_="foreignkey"
    )
    op.alter_column("exercise_attempts", "time_spent_ms", nullable=False)
    op.drop_column("exercise_attempts", "lesson_id")
    op.drop_column("exercise_attempts", "section_id")
    op.drop_column("exercise_attempts", "exercise_type")
    op.drop_column("exercise_attempts", "user_id")
