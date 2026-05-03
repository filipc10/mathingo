"""Czech vocative (pátý pád) for first names.

A small ported subset of the rules baked into the frontend's
czech-vocative dependency — Python has no equivalent on PyPI, and
pulling node-into-Python tooling for a 30-line transformation isn't
worth it. The trade-off is that uncommon names (especially foreign
ones) fall through to a generic consonant rule that may sound off
to a native speaker, but they degrade to a recognisable form rather
than crashing.

Examples:
    vocative("Filip")   -> "Filipe"
    vocative("Pavel")   -> "Pavle"
    vocative("Anna")    -> "Anno"
    vocative("Tomáš")   -> "Tomáši"
    vocative("Marie")   -> "Marie"   (no change)
    vocative("Petr")    -> "Petře"
"""

from __future__ import annotations


def vocative(name: str) -> str:
    if not name or len(name) < 2:
        return name

    lower = name.lower()
    last_two = lower[-2:]
    last_char = lower[-1]

    # Names ending in -e/-ě (Marie, Sofie, Anděla → Anděle handled below
    # via the -a rule) keep their nominative form.
    if last_char in ("e", "ě"):
        return name

    # Feminine -a → -o (Anna → Anno, Petra → Petro, Eva → Evo).
    if last_char == "a":
        return name[:-1] + "o"

    # Masculine -tr (Petr → Petře, Mistr → Mistře) before the generic
    # consonant rule, which would otherwise emit "Petre".
    if last_two == "tr":
        return name[:-2] + "tře"

    # Names ending -š (Tomáš → Tomáši) take -i, not the consonant -e.
    if last_char == "š":
        return name + "i"

    # -ek (Marek → Marku, Kubínek → Kubínku) and -el (Pavel → Pavle,
    # Karel → Karle) drop the e before the suffix.
    if last_two == "ek":
        return name[:-2] + "ku"
    if last_two == "el":
        return name[:-2] + "le"

    # Generic masculine consonant ending: append -e.
    if last_char in "bcdfghjklmnpqrstvwxz":
        return name + "e"

    # Vowel ending we didn't handle (-i, -o, -u, -y) — keep nominative.
    return name
