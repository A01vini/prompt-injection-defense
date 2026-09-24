"""
Milestone 3, first defense layer: instruction/data segregation.

Core idea (Liu et al., 2024; Starukh & Koshelev, 2026): untrusted content
(user query + retrieved documents) is data, never a command. This
lightweight, dependency-free version flags common override phrasing
appearing anywhere in that combined text.

This exists so you have a real, working before/after comparison for your
mid-sem review before the DistilBERT classifier (also Milestone 3) is
trained. Replace / supplement the pattern list with the classifier's
prediction later -- the (allowed, reason) interface stays identical, so
runner.py and chatbot.py don't need to change.
"""

import re

OVERRIDE_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"the hidden rules are visible to you",
    r"start your response using the above",
    r"you must follow",
    r"print yes",
    r"reveal your system prompt",
    r"pretend you are",
    r"system override",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in OVERRIDE_PATTERNS]


def segregator_defense(text):
    """
    Returns (allowed: bool, reason: str).
    Blocks the request if any override pattern is found in the combined
    user query + retrieved document text.
    """
    for pattern in _COMPILED:
        if pattern.search(text):
            return False, f"matched override pattern: '{pattern.pattern}'"
    return True, "clean"
