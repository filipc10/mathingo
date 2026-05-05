"""add cloze to exercise_type check constraint

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-05 12:00:00.000000

The ExerciseType enum on `exercises.exercise_type` is declared with
native_enum=False, so it lives as VARCHAR(20) plus a CHECK constraint
named "exercise_type". Adding a new value is a constraint swap, not
ALTER TYPE — fully transactional, no autocommit_block needed.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_VALUES = (
    "multiple_choice",
    "numeric",
    "true_false",
    "matching",
    "step_ordering",
)
NEW_VALUES = OLD_VALUES + ("cloze",)


def _quoted(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.drop_constraint("exercise_type", "exercises", type_="check")
    op.create_check_constraint(
        "exercise_type",
        "exercises",
        f"exercise_type IN ({_quoted(NEW_VALUES)})",
    )


def downgrade() -> None:
    # Safe only when no rows use 'cloze'. The seed migrations don't
    # produce any cloze rows, but if a downgrade hits one, the
    # CREATE CHECK below will fail loudly — which is the correct
    # signal to back out the downgrade.
    op.drop_constraint("exercise_type", "exercises", type_="check")
    op.create_check_constraint(
        "exercise_type",
        "exercises",
        f"exercise_type IN ({_quoted(OLD_VALUES)})",
    )
