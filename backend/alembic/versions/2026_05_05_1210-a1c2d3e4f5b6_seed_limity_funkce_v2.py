"""seed Limity funkce v2: 5 lessons × 6 exercises with mixed types

Revision ID: a1c2d3e4f5b6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-05 12:10:00.000000

Replaces the original 4-lesson / 10-exercise seed with a wider 5-lesson
arc that mirrors the 4MM101 syllabus on limits: pojem limity → limita
v bodě → limita v ∞ → Bolzano → l'Hospital. Each lesson is 6 exercises
mixing multiple_choice, numeric, true_false, matching, and step_ordering.

Strategy:
1. Locate the existing "Limity funkce" section (course_id=4MM101, order_index=1)
   and delete its lessons. ON DELETE CASCADE on exercises, lesson_attempts,
   exercise_attempts and user_lesson_progress sweeps the whole subtree.
2. Update the section's title/description in place.
3. Re-insert 5 lessons + 30 exercises with ON CONFLICT DO NOTHING so the
   migration is idempotent on re-run.

Old lesson_attempts / exercise_attempts (e.g. mock leaderboard rows pinned
to old exercise UUIDs) get cascaded out. Operators should re-run
backend/scripts/refresh_mock_xp.py afterwards to repopulate XP for mocks.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert as pg_insert


# revision identifiers, used by Alembic.
revision: str = "a1c2d3e4f5b6"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
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


# ---------- Content ----------

SECTION = {
    "order_index": 1,
    "title": "Limity funkce",
    "description": (
        "Pojem limity, jednostranné limity, limity v nekonečnu, "
        "Bolzanova věta a l'Hospitalovo pravidlo. Klíčové dovednosti "
        "pro úspěšné zvládnutí matematické analýzy v kurzu 4MM101."
    ),
}

LESSONS = [
    {
        "order_index": 1,
        "title": "Pojem limity a neurčité výrazy",
        "description": (
            "Vlastní vs. nevlastní bod, klasifikace neurčitých výrazů, "
            "limita geometrické posloupnosti."
        ),
        "xp_reward": 10,
    },
    {
        "order_index": 2,
        "title": "Limita funkce v bodě",
        "description": (
            "Vztah jednostranných limit, limita vs. spojitost, "
            "limita v bodě mimo definiční obor."
        ),
        "xp_reward": 10,
    },
    {
        "order_index": 3,
        "title": "Limity v nekonečnu",
        "description": (
            "Racionální funkce v nekonečnu, technika dělení nejvyšší mocninou."
        ),
        "xp_reward": 10,
    },
    {
        "order_index": 4,
        "title": "Bolzanova věta",
        "description": (
            "Předpoklady věty, jejich ověřování, dosah věty (existence, "
            "ne jednoznačnost)."
        ),
        "xp_reward": 10,
    },
    {
        "order_index": 5,
        "title": "L'Hospitalovo pravidlo",
        "description": (
            "Aplikovatelnost na neurčité výrazy 0/0 a ∞/∞, mechanika výpočtu."
        ),
        "xp_reward": 10,
    },
]

# exercises grouped by lesson order_index → list[dict]
EXERCISES = {
    # ---------- Lekce 1: Pojem limity a neurčité výrazy ----------
    1: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 1,
            "prompt": "Co je vlastní bod?",
            "explanation": (
                "Vlastní bod je libovolné reálné číslo. Body $+\\infty$ "
                "a $-\\infty$ se nazývají nevlastní."
            ),
            "payload": {
                "options": [
                    "Reálné číslo",
                    "$+\\infty$ nebo $-\\infty$",
                    "Bod, kde je funkce spojitá",
                    "Bod, kde funkce má limitu",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "multiple_choice",
            "difficulty": 1,
            "prompt": "Které z následujících je nevlastní bod?",
            "explanation": (
                "Pouze $+\\infty$ a $-\\infty$ jsou nevlastní body. Všechna "
                "konečná reálná čísla, byť jakkoliv velká, jsou vlastní."
            ),
            "payload": {
                "options": [
                    "$+\\infty$",
                    "$0$",
                    "$\\frac{1}{2}$",
                    "$-1\\,000\\,000$",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 3,
            "exercise_type": "matching",
            "difficulty": 3,
            "prompt": "Přiřaď výraz k tomu, zda je definovaný, nebo neurčitý:",
            "explanation": (
                "Součiny a součty stejnoznačných nekonečen jsou definované. "
                "Rozdíl stejnoznačných nekonečen a součin nuly s nekonečnem "
                "jsou neurčité — výsledek závisí na konkrétních posloupnostech."
            ),
            "payload": {
                "items": [
                    "$-\\infty + \\infty$",
                    "$+\\infty \\cdot (+\\infty)$",
                    "$0 \\cdot \\infty$",
                    "$-\\infty + (-\\infty)$",
                ],
                "categories": ["Definovaný", "Neurčitý"],
                "instructions": "Klepni na výraz a poté na kategorii.",
                "assignments": {
                    "$-\\infty + \\infty$": "Neurčitý",
                    "$+\\infty \\cdot (+\\infty)$": "Definovaný",
                    "$0 \\cdot \\infty$": "Neurčitý",
                    "$-\\infty + (-\\infty)$": "Definovaný",
                },
            },
        },
        {
            "order_index": 4,
            "exercise_type": "true_false",
            "difficulty": 1,
            "prompt": "Výraz $\\frac{0}{0}$ je neurčitý.",
            "explanation": (
                "Ano, $\\frac{0}{0}$ je klasický neurčitý výraz. Limita podílu, "
                "kde čitatel i jmenovatel jdou k nule, může vyjít cokoliv "
                "(záleží na rychlosti)."
            ),
            "payload": {"value": True},
        },
        {
            "order_index": 5,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "Doplňte: Geometrická posloupnost $q^n$ má pro $|q| < 1$ "
                "limitu rovnu ___."
            ),
            "explanation": (
                "Pro $|q| < 1$ jdou mocniny $q^n$ k nule. Pro $q = 1$ je "
                "limita 1, pro $q > 1$ diverguje k $+\\infty$, pro "
                "$q \\le -1$ neexistuje."
            ),
            "payload": {
                "options": ["$0$", "$1$", "$+\\infty$", "neexistuje"],
                "correct_index": 0,
            },
        },
        {
            "order_index": 6,
            "exercise_type": "true_false",
            "difficulty": 2,
            "prompt": "Pokud $q < 0$, limita posloupnosti $q^n$ vždy existuje.",
            "explanation": (
                "Pro $q \\in (-1, 0)$ limita existuje (= 0). Pro $q \\le -1$ "
                "ale posloupnost osciluje a limita neexistuje. Příklad: "
                "$(-1)^n$ střídavě dává 1 a $-1$."
            ),
            "payload": {"value": False},
        },
    ],
    # ---------- Lekce 2: Limita funkce v bodě ----------
    2: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": "Funkce $f$ má v bodě $c$ limitu právě tehdy, když:",
            "explanation": (
                "Limita existuje právě tehdy, když se obě jednostranné limity "
                "rovnají. Spojitost je silnější vlastnost — vyžaduje navíc, "
                "aby limita byla rovna $f(c)$."
            ),
            "payload": {
                "options": [
                    (
                        "Pravostranná a levostranná limita v bodě $c$ existují "
                        "a jsou si rovny"
                    ),
                    "Funkce je v bodě $c$ spojitá",
                    "Bod $c$ patří do $D(f)$",
                    "$f(c)$ je definováno",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "true_false",
            "difficulty": 1,
            "prompt": "Pokud je funkce spojitá v bodě $c$, pak má v bodě $c$ limitu.",
            "explanation": (
                "Spojitost v bodě je definována jako "
                "$\\lim_{x \\to c} f(x) = f(c)$. Existence limity je tedy "
                "nutnou podmínkou spojitosti."
            ),
            "payload": {"value": True},
        },
        {
            "order_index": 3,
            "exercise_type": "true_false",
            "difficulty": 2,
            "prompt": "Pokud má funkce v bodě $c$ limitu, pak je v něm spojitá.",
            "explanation": (
                "Limita může existovat, i když $c \\notin D(f)$ "
                "(např. $\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$, ale 0 v "
                "$D(f)$ není), nebo když $f(c)$ existuje, ale není rovno "
                "limitě (odstranitelná nespojitost)."
            ),
            "payload": {"value": False},
        },
        {
            "order_index": 4,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": "Limita funkce $f$ v bodě $c$ může existovat, i když:",
            "explanation": (
                "Klasický příklad: $f(x) = \\frac{\\sin x}{x}$ není definována "
                "v 0, ale $\\lim_{x \\to 0} f(x) = 1$ existuje. Limita zkoumá "
                "chování v okolí bodu, ne v bodě samotném."
            ),
            "payload": {
                "options": [
                    "$c$ nepatří do definičního oboru $f$",
                    "Funkce není zdola omezena",
                    "Funkce není shora omezena",
                    "$f(c) = 0$",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 5,
            "exercise_type": "numeric",
            "difficulty": 1,
            "prompt": "Vypočti: $\\lim_{x \\to 2} (3x + 1) = $ ___",
            "explanation": (
                "Lineární funkce je všude spojitá, proto stačí dosadit: "
                "$3 \\cdot 2 + 1 = 7$."
            ),
            "payload": {"expected": 7, "tolerance": 0},
        },
        {
            "order_index": 6,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "Která elementární funkce má pro $x \\to -\\infty$ limitu rovnu 0?"
            ),
            "explanation": (
                "$e^x \\to 0$ pro $x \\to -\\infty$. $\\ln x$ pro "
                "$x \\to -\\infty$ není ani definována, $x^2 \\to +\\infty$, "
                "a $\\sin x$ osciluje mezi $-1$ a 1 (limita neexistuje)."
            ),
            "payload": {
                "options": ["$e^x$", "$\\ln x$", "$x^2$", "$\\sin x$"],
                "correct_index": 0,
            },
        },
    ],
    # ---------- Lekce 3: Limity v nekonečnu ----------
    3: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "$\\displaystyle\\lim_{x \\to \\infty} \\frac{x^2 + 1}{x + 5} = $"
            ),
            "explanation": (
                "Stupeň čitatele (2) je vyšší než stupeň jmenovatele (1), "
                "proto limita diverguje k $+\\infty$."
            ),
            "payload": {
                "options": ["$+\\infty$", "$0$", "$1$", "neexistuje"],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "$\\displaystyle\\lim_{x \\to \\infty} \\frac{2x + 3}{5x - 1} = $"
            ),
            "explanation": (
                "Stejné stupně v čitateli i jmenovateli (1) — limita je podíl "
                "koeficientů u nejvyšších mocnin: $\\frac{2}{5}$."
            ),
            "payload": {
                "options": ["$\\frac{2}{5}$", "$0$", "$+\\infty$", "$1$"],
                "correct_index": 0,
            },
        },
        {
            "order_index": 3,
            "exercise_type": "numeric",
            "difficulty": 1,
            "prompt": "$\\displaystyle\\lim_{x \\to \\infty} \\frac{1}{x} = $",
            "explanation": (
                "Pro $x \\to \\infty$ jde $\\frac{1}{x}$ k nule shora. Toto je "
                "základní limita pro výpočty technikou dělení nejvyšší mocninou."
            ),
            "payload": {"expected": 0, "tolerance": 0},
        },
        {
            "order_index": 4,
            "exercise_type": "step_ordering",
            "difficulty": 3,
            "prompt": (
                "Seřaď kroky výpočtu "
                "$\\displaystyle\\lim_{x \\to \\infty} \\frac{3x^2 + 2x}{x^2 - 5}$:"
            ),
            "explanation": (
                "Standardní postup u racionálních funkcí v nekonečnu: "
                "identifikovat nejvyšší stupeň, vydělit, využít "
                "$\\lim_{x \\to \\infty} \\frac{1}{x^k} = 0$, vyhodnotit."
            ),
            "payload": {
                "steps": [
                    {
                        "id": "s1",
                        "text": (
                            "Identifikuj nejvyšší mocninu v čitateli "
                            "a jmenovateli (zde $x^2$)"
                        ),
                    },
                    {
                        "id": "s2",
                        "text": "Vyděl čitatele i jmenovatele $x^2$",
                    },
                    {
                        "id": "s3",
                        "text": (
                            "Dosaď za $x \\to \\infty$: členy s "
                            "$\\frac{1}{x}$ a $\\frac{1}{x^2}$ jdou k 0"
                        ),
                    },
                    {
                        "id": "s4",
                        "text": "Výsledek: $\\frac{3 + 0}{1 - 0} = 3$",
                    },
                ],
                "instructions": "Použij šipky vpravo k seřazení.",
                "order": ["s1", "s2", "s3", "s4"],
            },
        },
        {
            "order_index": 5,
            "exercise_type": "true_false",
            "difficulty": 2,
            "prompt": (
                "Pro racionální funkci, kde stupeň čitatele je menší než "
                "stupeň jmenovatele, je limita v nekonečnu rovna 0."
            ),
            "explanation": (
                "Při dělení nejvyšší mocninou jmenovatele dostaneme v čitateli "
                "členy se zápornými mocninami $x$, které jdou k 0. Ve jmenovateli "
                "zůstane konstantní člen."
            ),
            "payload": {"value": True},
        },
        {
            "order_index": 6,
            "exercise_type": "matching",
            "difficulty": 3,
            "prompt": "Přiřaď limitu racionální funkce v nekonečnu:",
            "explanation": (
                "Pravidlo: stupeň čitatele $>$ stupeň jmenovatele $\\to \\pm\\infty$; "
                "rovné stupně $\\to$ podíl vedoucích koeficientů; "
                "stupeň čitatele $<$ jmenovatele $\\to 0$."
            ),
            "payload": {
                "items": [
                    "$\\lim_{x \\to \\infty} \\frac{x^3}{x^2}$",
                    "$\\lim_{x \\to \\infty} \\frac{x^2}{x^3}$",
                    "$\\lim_{x \\to \\infty} \\frac{2x^3}{5x^3}$",
                    "$\\lim_{x \\to \\infty} \\frac{x^4}{x^4 + 1}$",
                ],
                "categories": ["$0$", "$\\frac{2}{5}$", "$1$", "$+\\infty$"],
                "instructions": "Přiřaď každou limitu k její hodnotě.",
                "assignments": {
                    "$\\lim_{x \\to \\infty} \\frac{x^3}{x^2}$": "$+\\infty$",
                    "$\\lim_{x \\to \\infty} \\frac{x^2}{x^3}$": "$0$",
                    "$\\lim_{x \\to \\infty} \\frac{2x^3}{5x^3}$": "$\\frac{2}{5}$",
                    "$\\lim_{x \\to \\infty} \\frac{x^4}{x^4 + 1}$": "$1$",
                },
            },
        },
    ],
    # ---------- Lekce 4: Bolzanova věta ----------
    4: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "Doplň větu: Nechť $f$ je ___ funkce na uzavřeném intervalu "
                "$\\langle a, b \\rangle$ a navíc platí "
                "$f(a) \\cdot f(b) < 0$, pak existuje $c \\in (a, b)$ tak, "
                "že $f(c) = 0$."
            ),
            "explanation": (
                "Klíčový předpoklad Bolzanovy věty je spojitost na uzavřeném "
                "intervalu. Diferencovatelnost není potřeba (a v některých "
                "bodech ani nemusí existovat)."
            ),
            "payload": {
                "options": [
                    "spojitá",
                    "rostoucí",
                    "omezená",
                    "diferencovatelná",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "true_false",
            "difficulty": 1,
            "prompt": (
                "Pokud $f(a) \\cdot f(b) < 0$, znamená to, že hodnoty "
                "$f(a)$ a $f(b)$ mají různá znaménka."
            ),
            "explanation": (
                "Součin dvou reálných čísel je záporný právě tehdy, když mají "
                "opačná znaménka. Toto je geometrické srdce Bolzanovy věty: "
                "graf přechází z poloroviny pod osu $x$ do poloroviny nad ní."
            ),
            "payload": {"value": True},
        },
        {
            "order_index": 3,
            "exercise_type": "multiple_choice",
            "difficulty": 3,
            "prompt": (
                "Funkce $f(x) = -2x + 1$ na intervalu $\\langle -3, 5 \\rangle$ "
                "splňuje předpoklady Bolzanovy věty?"
            ),
            "explanation": (
                "Lineární funkce je spojitá všude. Hodnoty v krajních bodech "
                "mají opačná znaménka, takže Bolzanova věta zaručuje existenci "
                "kořene mezi $-3$ a 5 (konkrétně $x = 0{,}5$)."
            ),
            "payload": {
                "options": [
                    "Ano: funkce je spojitá, $f(-3) = 7 > 0$, $f(5) = -9 < 0$",
                    "Ne, funkce není spojitá",
                    "Ne, $f(-3)$ a $f(5)$ mají stejná znaménka",
                    "Nelze rozhodnout bez výpočtu derivace",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 4,
            "exercise_type": "matching",
            "difficulty": 4,
            "prompt": (
                "Přiřaď, zda funkce na daném intervalu splňuje předpoklady "
                "Bolzanovy věty:"
            ),
            "explanation": (
                "Předpoklady jsou dva: spojitost na uzavřeném intervalu a "
                "opačná znaménka v krajních bodech. Stačí jeden předpoklad "
                "porušit a věta neplatí."
            ),
            "payload": {
                "items": [
                    "$f(x) = x^2$ na $\\langle -2, 2 \\rangle$",
                    "$f(x) = x^3 + x - 1$ na $\\langle 0, 1 \\rangle$",
                    "$f(x) = \\frac{1}{x}$ na $\\langle -1, 1 \\rangle$",
                    "$f(x) = \\ln x - 1$ na $\\langle 1, e^2 \\rangle$",
                ],
                "categories": ["Splňuje", "Nesplňuje"],
                "instructions": "Klepni na funkci a poté na kategorii.",
                "assignments": {
                    "$f(x) = x^2$ na $\\langle -2, 2 \\rangle$": "Nesplňuje",
                    "$f(x) = x^3 + x - 1$ na $\\langle 0, 1 \\rangle$": "Splňuje",
                    "$f(x) = \\frac{1}{x}$ na $\\langle -1, 1 \\rangle$": "Nesplňuje",
                    "$f(x) = \\ln x - 1$ na $\\langle 1, e^2 \\rangle$": "Splňuje",
                },
            },
        },
        {
            "order_index": 5,
            "exercise_type": "true_false",
            "difficulty": 3,
            "prompt": (
                "Bolzanova věta tvrdí, že pokud jsou splněny její předpoklady, "
                "existuje **přesně jeden** kořen rovnice $f(x) = 0$ na "
                "intervalu $(a, b)$."
            ),
            "explanation": (
                "Bolzanova věta zaručuje alespoň jeden kořen, ne přesně jeden. "
                "Funkce může na intervalu mít více kořenů (např. $\\sin x$ na "
                "$\\langle 0, 4\\pi \\rangle$ má víc nul)."
            ),
            "payload": {"value": False},
        },
        {
            "order_index": 6,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": "Bolzanova věta zajišťuje:",
            "explanation": (
                "Bolzanova věta je věta o existenci, ne o jednoznačnosti ani "
                "o monotonii. Pro maximum/minimum slouží Weierstrassova věta."
            ),
            "payload": {
                "options": [
                    "Existenci alespoň jednoho kořene rovnice $f(x) = 0$ na $(a, b)$",
                    "Existenci přesně jednoho kořene",
                    "Že funkce je rostoucí",
                    "Že funkce nabývá maxima a minima",
                ],
                "correct_index": 0,
            },
        },
    ],
    # ---------- Lekce 5: L'Hospitalovo pravidlo ----------
    5: [
        {
            "order_index": 1,
            "exercise_type": "multiple_choice",
            "difficulty": 2,
            "prompt": (
                "L'Hospitalovo pravidlo lze přímo aplikovat na limitu, "
                "která vede k výrazu typu:"
            ),
            "explanation": (
                "L'Hospital se přímo aplikuje pouze na typy $\\frac{0}{0}$ a "
                "$\\frac{\\infty}{\\infty}$. Jiné neurčité výrazy "
                "($0 \\cdot \\infty$, $\\infty - \\infty$, $1^{\\infty}$, ...) "
                "je nutné nejdřív upravit na podíl."
            ),
            "payload": {
                "options": [
                    "$\\frac{0}{0}$ nebo $\\frac{\\infty}{\\infty}$",
                    "$0 \\cdot 0$",
                    "$\\infty - \\infty$",
                    "Jakýkoliv neurčitý výraz",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 2,
            "exercise_type": "matching",
            "difficulty": 3,
            "prompt": "Přiřaď limitu k typu neurčitého výrazu (před úpravou):",
            "explanation": (
                "Před aplikací l'Hospitala vždy nejprve klasifikuj typ "
                "neurčitosti — určuje, jestli se l'Hospital dá vůbec použít "
                "a jak budeš upravovat."
            ),
            "payload": {
                "items": [
                    "$\\lim_{x \\to 0} \\frac{\\sin x}{x}$",
                    "$\\lim_{x \\to \\infty} \\frac{x^3}{e^x}$",
                    "$\\lim_{x \\to \\infty} \\frac{\\ln x}{x}$",
                    "$\\lim_{x \\to 1} \\frac{x^2 - 1}{x - 1}$",
                ],
                "categories": ["$\\frac{0}{0}$", "$\\frac{\\infty}{\\infty}$"],
                "instructions": "Klasifikuj každou limitu před úpravou.",
                "assignments": {
                    "$\\lim_{x \\to 0} \\frac{\\sin x}{x}$": "$\\frac{0}{0}$",
                    "$\\lim_{x \\to \\infty} \\frac{x^3}{e^x}$": (
                        "$\\frac{\\infty}{\\infty}$"
                    ),
                    "$\\lim_{x \\to \\infty} \\frac{\\ln x}{x}$": (
                        "$\\frac{\\infty}{\\infty}$"
                    ),
                    "$\\lim_{x \\to 1} \\frac{x^2 - 1}{x - 1}$": "$\\frac{0}{0}$",
                },
            },
        },
        {
            "order_index": 3,
            "exercise_type": "true_false",
            "difficulty": 3,
            "prompt": (
                "Limita $\\lim_{x \\to 3} \\frac{x^2 + 6}{x^2 - 9}$ vede k "
                "výrazu $\\frac{15}{0}$, takže lze l'Hospitalovo pravidlo "
                "aplikovat."
            ),
            "explanation": (
                "$\\frac{15}{0}$ není neurčitý výraz — je to forma "
                "$\\frac{c}{0}$, která vede k $\\pm\\infty$ podle znaménka, "
                "ne k l'Hospitalovi. L'Hospital vyžaduje $\\frac{0}{0}$ "
                "nebo $\\frac{\\infty}{\\infty}$."
            ),
            "payload": {"value": False},
        },
        {
            "order_index": 4,
            "exercise_type": "multiple_choice",
            "difficulty": 3,
            "prompt": "U které limity NELZE l'Hospitalovo pravidlo přímo aplikovat?",
            "explanation": (
                "První limita vede k $\\frac{1}{0}$, což není neurčitý výraz "
                "pro l'Hospitala. Ostatní jsou typu $\\frac{0}{0}$ nebo "
                "$\\frac{\\infty}{\\infty}$."
            ),
            "payload": {
                "options": [
                    "$\\lim_{x \\to 1} \\frac{x^2}{x - 1}$",
                    "$\\lim_{x \\to 0} \\frac{\\sin x}{x}$",
                    "$\\lim_{x \\to \\infty} \\frac{e^x}{x^2}$",
                    "$\\lim_{x \\to 0} \\frac{1 - \\cos x}{x^2}$",
                ],
                "correct_index": 0,
            },
        },
        {
            "order_index": 5,
            "exercise_type": "step_ordering",
            "difficulty": 3,
            "prompt": (
                "Seřaď kroky aplikace l'Hospitalova pravidla na "
                "$\\lim_{x \\to 0} \\frac{\\sin x}{x}$:"
            ),
            "explanation": (
                "L'Hospital není zkratka — vždy nejdřív ověř typ neurčitosti, "
                "pak derivuj odděleně čitatele a jmenovatele (NE jako podíl!), "
                "a vypočítej limitu nového podílu."
            ),
            "payload": {
                "steps": [
                    {
                        "id": "s1",
                        "text": (
                            "Ověř, že limita vede k neurčitému výrazu typu "
                            "$\\frac{0}{0}$ (zde $\\frac{\\sin 0}{0} = "
                            "\\frac{0}{0}$)"
                        ),
                    },
                    {
                        "id": "s2",
                        "text": (
                            "Spočítej derivaci čitatele: "
                            "$(\\sin x)' = \\cos x$"
                        ),
                    },
                    {
                        "id": "s3",
                        "text": "Spočítej derivaci jmenovatele: $(x)' = 1$",
                    },
                    {
                        "id": "s4",
                        "text": (
                            "Vypočti limitu nového podílu: "
                            "$\\lim_{x \\to 0} \\frac{\\cos x}{1} = 1$"
                        ),
                    },
                ],
                "instructions": "Použij šipky vpravo k seřazení.",
                "order": ["s1", "s2", "s3", "s4"],
            },
        },
        {
            "order_index": 6,
            "exercise_type": "numeric",
            "difficulty": 3,
            "prompt": "Vypočti $\\lim_{x \\to 0} \\frac{\\sin 3x}{x}$",
            "explanation": (
                "L'Hospital: $\\frac{(\\sin 3x)'}{(x)'} = "
                "\\frac{3 \\cos 3x}{1}$, dosaď $x = 0$: $3 \\cdot 1 = 3$. "
                "Alternativně: $\\frac{\\sin 3x}{x} = 3 \\cdot "
                "\\frac{\\sin 3x}{3x}$ a využij známé "
                "$\\lim \\frac{\\sin u}{u} = 1$."
            ),
            "payload": {"expected": 3, "tolerance": 0},
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

    section_id = bind.execute(
        sa.select(sections.c.id).where(
            sections.c.course_id == course_id,
            sections.c.order_index == SECTION["order_index"],
        )
    ).scalar_one_or_none()

    if section_id is not None:
        # Wipe old lessons; CASCADE handles exercises, lesson_attempts,
        # exercise_attempts and user_lesson_progress automatically.
        bind.execute(sa.delete(lessons).where(lessons.c.section_id == section_id))
        # Update section metadata in place — keep the same id so
        # course_progress URLs and bookmarks survive.
        bind.execute(
            sa.update(sections)
            .where(sections.c.id == section_id)
            .values(title=SECTION["title"], description=SECTION["description"])
        )
    else:
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
    # The previous content was destroyed in upgrade(), so a true restore
    # isn't possible from this migration alone. Downgrading here just
    # clears the v2 lessons; if an operator needs the v1 content back,
    # they need to also `alembic downgrade f4ed5e40904a` and re-upgrade,
    # which will re-seed the original 4 lessons / 10 exercises.
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

    bind.execute(sa.delete(lessons).where(lessons.c.section_id == section_id))
