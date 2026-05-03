"""Notification copy pool and selection logic.

Three categories × six lines = 18 templates. The pool design choices
are deliberate guardrails against habitual dark patterns:

- No streak fear ("Ztratíš svůj streak!")
- No FOMO / social compare ("Tvoji spolužáci tě předbíhají")
- No guilt trip ("Jsem na tebe smutný")
- No vague urgency ("Last chance!")

The 7-day anti-repetition pool keys on the raw template (with the
{name} placeholder still present) so renames don't fool the dedupe.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.models import User
from app.services.vocative import vocative

WITH_NAME: list[str] = [
    "{name}, máš na limity 5 minut? 🧮",
    "{name}, dneska jsme se ještě neviděli! 👋",
    "{name}, drobná lekce dnes? 🌱",
    "Hej {name}, krátká rozcvička? ✏️",
    "{name}, co takhle pár příkladů? 📐",
    "{name}, dáme dneska aspoň 5 minut? ⏱️",
]

NEUTRAL: list[str] = [
    "Ještě ses tu dnes neukázal/a 👀",
    "Krátká lekce na uvolnění hlavy? ☕",
    "Dnešní procvičování čeká! 📚",
    "Pár minut pro tvůj mozek 🧠",
    "Drobné cvičení dneska? ✨",
    "Otevři aplikaci a podívej, co tě čeká 🎯",
]

QUESTION: list[str] = [
    "Co tvoje denní lekce matematiky? 🤔",
    "Máš teď chvilku na pár příkladů?",
    "Limity nebo derivace dnes?",
    "Jak na tom dneska s motivací? 💪",
    "Najdeš 5 minut pro matematiku?",
    "Připraven/a na další lekci?",
]


def _all_templates() -> list[str]:
    return [*WITH_NAME, *NEUTRAL, *QUESTION]


@dataclass(frozen=True)
class NotificationCopy:
    """Result of a pick. `template` is the raw form (with {name} still
    in place if any) — that's what gets persisted in NotificationLog so
    anti-repetition keys on the same value the picker chose. `body` is
    the rendered text shown in the push notification.
    """

    title: str
    body: str
    template: str


def pick_notification_text(
    user: User,
    recent_templates: list[str],
    *,
    rng: random.Random | None = None,
) -> NotificationCopy:
    """Choose a notification line for `user`, avoiding recent repeats.

    `recent_templates` is the set of raw templates this user has seen
    in the anti-repetition window (typically last 7 days). If every
    template in the pool falls into that window the filter resets so
    the user still gets *something* — better a stale repeat than a
    silent miss. `rng` exists so tests can pin the choice.
    """
    chooser = rng or random
    pool = _all_templates()
    recent_set = set(recent_templates)

    available = [t for t in pool if t not in recent_set]
    if not available:
        available = pool

    template = chooser.choice(available)

    if "{name}" in template:
        body = template.replace("{name}", vocative(user.first_name or "Mathingo"))
    else:
        body = template

    return NotificationCopy(title="Mathingo", body=body, template=template)
