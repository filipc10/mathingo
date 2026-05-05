"""Unit tests for the per-type branches of `_evaluate()`.

Exercises a stand-in object instead of a real ORM Exercise — `_evaluate`
only reads `exercise_type`, `id`, and `payload`, so SimpleNamespace is
all it needs and skips the DB / event loop overhead the rest of the
test suite carries.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "")
os.environ.setdefault("RESEND_API_KEY", "test")
os.environ.setdefault("APP_URL", "http://test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test")

from fastapi import HTTPException  # noqa: E402

from app.api.content import _evaluate  # noqa: E402


def make_exercise(exercise_type: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        exercise_type=exercise_type,
        payload=payload,
    )


# ---------- cloze ----------


def test_cloze_exact_match():
    ex = make_exercise("cloze", {"value": "spojitá"})
    correct, expected = _evaluate(ex, "spojitá")
    assert correct is True
    assert expected == "spojitá"


def test_cloze_case_insensitive_default():
    ex = make_exercise("cloze", {"value": "spojitá"})
    assert _evaluate(ex, "SPOJITÁ")[0] is True
    assert _evaluate(ex, "Spojitá")[0] is True


def test_cloze_trim_whitespace_default():
    ex = make_exercise("cloze", {"value": "spojitá"})
    assert _evaluate(ex, "  spojitá  ")[0] is True


def test_cloze_alternates_accepted():
    ex = make_exercise(
        "cloze",
        {"value": "spojitá", "alternates": ["spojita", "spojity"]},
    )
    assert _evaluate(ex, "spojita")[0] is True
    assert _evaluate(ex, "spojity")[0] is True


def test_cloze_wrong_answer():
    ex = make_exercise("cloze", {"value": "spojitá"})
    assert _evaluate(ex, "diferencovatelná")[0] is False


def test_cloze_empty_input():
    ex = make_exercise("cloze", {"value": "spojitá"})
    assert _evaluate(ex, "")[0] is False
    assert _evaluate(ex, "   ")[0] is False


def test_cloze_case_sensitive_flag_respected():
    ex = make_exercise(
        "cloze",
        {"value": "Foo", "case_sensitive": True},
    )
    assert _evaluate(ex, "Foo")[0] is True
    assert _evaluate(ex, "foo")[0] is False
    assert _evaluate(ex, "FOO")[0] is False


def test_cloze_non_string_rejected():
    ex = make_exercise("cloze", {"value": "x"})
    with pytest.raises(HTTPException) as excinfo:
        _evaluate(ex, 42)
    assert excinfo.value.status_code == 422


# ---------- true_false ----------


def test_true_false_correct_true():
    ex = make_exercise("true_false", {"value": True})
    correct, expected = _evaluate(ex, True)
    assert correct is True
    assert expected is True


def test_true_false_correct_false():
    ex = make_exercise("true_false", {"value": False})
    assert _evaluate(ex, False) == (True, False)


def test_true_false_wrong():
    ex = make_exercise("true_false", {"value": True})
    assert _evaluate(ex, False)[0] is False


def test_true_false_int_rejected():
    # bool is a subclass of int — strict isinstance(bool) check rejects.
    ex = make_exercise("true_false", {"value": True})
    with pytest.raises(HTTPException) as excinfo:
        _evaluate(ex, 1)
    assert excinfo.value.status_code == 422


def test_true_false_string_rejected():
    ex = make_exercise("true_false", {"value": True})
    with pytest.raises(HTTPException) as excinfo:
        _evaluate(ex, "true")
    assert excinfo.value.status_code == 422


# ---------- matching ----------


def test_matching_full_correct():
    payload = {
        "items": ["a", "b"],
        "categories": ["X", "Y"],
        "assignments": {"a": "X", "b": "Y"},
    }
    ex = make_exercise("matching", payload)
    correct, expected = _evaluate(ex, {"a": "X", "b": "Y"})
    assert correct is True
    assert expected == {"a": "X", "b": "Y"}


def test_matching_wrong_assignment():
    payload = {"items": ["a"], "categories": ["X", "Y"], "assignments": {"a": "X"}}
    ex = make_exercise("matching", payload)
    assert _evaluate(ex, {"a": "Y"})[0] is False


def test_matching_partial_assignments():
    payload = {
        "items": ["a", "b"],
        "categories": ["X"],
        "assignments": {"a": "X", "b": "X"},
    }
    ex = make_exercise("matching", payload)
    assert _evaluate(ex, {"a": "X"})[0] is False


def test_matching_non_dict_rejected():
    payload = {"items": ["a"], "categories": ["X"], "assignments": {"a": "X"}}
    ex = make_exercise("matching", payload)
    with pytest.raises(HTTPException) as excinfo:
        _evaluate(ex, ["a", "X"])
    assert excinfo.value.status_code == 422


# ---------- step_ordering ----------


def test_step_ordering_correct():
    ex = make_exercise("step_ordering", {"order": ["s1", "s2", "s3"]})
    correct, expected = _evaluate(ex, ["s1", "s2", "s3"])
    assert correct is True
    assert expected == ["s1", "s2", "s3"]


def test_step_ordering_wrong():
    ex = make_exercise("step_ordering", {"order": ["s1", "s2", "s3"]})
    assert _evaluate(ex, ["s2", "s1", "s3"])[0] is False


def test_step_ordering_partial_rejected():
    ex = make_exercise("step_ordering", {"order": ["s1", "s2", "s3"]})
    assert _evaluate(ex, ["s1", "s2"])[0] is False


def test_step_ordering_non_list_rejected():
    ex = make_exercise("step_ordering", {"order": ["s1"]})
    with pytest.raises(HTTPException) as excinfo:
        _evaluate(ex, "s1")
    assert excinfo.value.status_code == 422
