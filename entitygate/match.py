"""Brand-anchor entity matching.

The core idea, generalized from a real production bug (see the README's
"where this came from"): a candidate string plausibly belongs to an
entity only if the entity's own DISTINCTIVE name token literally occurs
inside it. Not semantic similarity, not an LLM's judgment call -- a
literal substring check on the one token that actually identifies the
brand, because semantic/token-overlap approaches were tried first and
demonstrably fail on real data (see tests/test_match.py for the exact
real collisions this protects against).
"""
from __future__ import annotations

import re

# Generic words that appear in many unrelated legal/business names and
# therefore carry no identifying signal on their own -- without this list,
# "Apollo Hospitals" and "Kauvery Hospital" collide on the shared word
# "hospital(s)", a real, confirmed false-positive class.
STOPWORDS = frozenset({
    "the", "and", "for", "ltd", "limited", "inc", "corp", "corporation", "pvt", "private",
    "llc", "llp", "plc", "gmbh", "company", "companies", "group", "groups", "holdings",
    "international", "global", "india", "solutions", "services", "technologies",
    "hospital", "hospitals", "healthcare", "clinic", "clinics",
})

# A token at least this long is treated as distinctive enough to stand on
# its own. Below this length, a second corroborating token is required --
# "Sri" alone must not bridge "Sri Krishna Sweets" to an unrelated
# "Srivenkateswara"; "Prashanth" alone is fine, nothing else real shares it.
DISTINCTIVE_ANCHOR_LEN = 6


def _tokens(entity: str) -> list[str]:
    """Significant tokens, in order -- order matters, the first surviving
    token is the brand anchor."""
    return [
        tok for tok in re.sub(r"[^a-z0-9]+", " ", entity.lower()).split()
        if len(tok) >= 3 and tok not in STOPWORDS
    ]


def matches_entity(candidate: str, entity: str) -> bool:
    """True if `candidate` (a handle, slug, URL path, or any short
    identifier string) plausibly belongs to `entity`.

    Rule: the entity's first significant token (its brand anchor) must
    occur inside `candidate`. If that anchor is short/common
    (< DISTINCTIVE_ANCHOR_LEN chars), a second token from the entity name
    must ALSO occur in `candidate` -- otherwise the anchor alone is
    sufficient.

    Two alternatives were tried first and are demonstrably wrong on real
    data (see tests/test_match.py):
      - "any significant token matches" -- bridges unrelated companies
        that share one generic industry word.
      - "every token must match" -- rejects genuinely correct real-world
        identifiers that keep the brand and drop part of the legal name
        (e.g. "prashanth-multispeciality" for "Prashanth Hospitals Pvt
        Ltd").

    An entity with no usable tokens (empty, or only stopwords) fails
    closed: nothing is accepted for it.
    """
    tokens = _tokens(entity)
    if not tokens:
        return False
    flat = re.sub(r"[^a-z0-9]+", "", candidate.lower())
    anchor = tokens[0]
    if not flat or anchor not in flat:
        return False
    if len(anchor) < DISTINCTIVE_ANCHOR_LEN and len(tokens) >= 2:
        return any(tok in flat for tok in tokens[1:])
    return True
