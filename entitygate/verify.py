"""verify_claim -- the full gate: shape (optional) + verbatim presence +
entity-anchor match. All three must pass before a candidate fact is
trusted as belonging to the entity it's claimed to describe.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .match import matches_entity

Reason = str  # "ok" | "no_shape_match" | "not_verbatim_in_source" | "no_entity_match"


@dataclass
class VerificationResult:
    """`verified` is the one field most callers need. `reason` explains a
    rejection -- useful for the benchmark (which failure class fired) and
    for debugging why a real, correct candidate got rejected."""

    verified: bool
    reason: Reason
    candidate: str
    entity: str


def verify_claim(
    candidate: str,
    entity: str,
    source_text: str,
    shape: Callable[[str], bool] | None = None,
) -> VerificationResult:
    """Three independent gates, in order, short-circuiting on the first
    failure:

    1. Shape (optional): if `shape` is given, `candidate` must satisfy it
       -- e.g. "parses as a real Instagram profile URL, not a post link."
       Skipped entirely if no shape function is supplied; not every use
       case has a platform-specific shape to check.
    2. Verbatim presence: `candidate` must appear in `source_text`,
       case-insensitively, exactly as given. This is what every generic
       hallucination/fabrication checker already does in some form --
       kept here because it's a real, necessary (not sufficient)
       precondition, not because it's novel.
    3. Entity match (the actual point of this library): `candidate` must
       plausibly belong to `entity`, via matches_entity's brand-anchor
       rule -- the check groundedness/faithfulness tooling does not do,
       because the candidate being real and present in the source says
       nothing about WHOSE it is.
    """
    if shape is not None and not shape(candidate):
        return VerificationResult(False, "no_shape_match", candidate, entity)
    if candidate.lower() not in source_text.lower():
        return VerificationResult(False, "not_verbatim_in_source", candidate, entity)
    if not matches_entity(candidate, entity):
        return VerificationResult(False, "no_entity_match", candidate, entity)
    return VerificationResult(True, "ok", candidate, entity)
