"""entitygate -- catch entity misattribution in LLM-extracted facts.

Most hallucination tooling asks "is this claim true / supported by the
source." That's necessary but not sufficient: a claim can be perfectly
real, perfectly grounded in the retrieved text, and still belong to the
WRONG entity -- a third party cited as a source gets attributed to the
subject, a name-collision competitor from an unrelated industry gets
accepted, a lookalike account gets measured instead of the real one.
Groundedness checkers say yes to all of these, because the fact really
is in the context. entitygate asks the question groundedness checkers
don't: does this fact actually belong to the entity it's claimed to
belong to.

Public API:
    matches_entity(candidate, entity) -> bool
    verify_claim(candidate, entity, source_text, shape=None) -> VerificationResult
"""
from .match import matches_entity
from .verify import VerificationResult, verify_claim

__all__ = ["matches_entity", "verify_claim", "VerificationResult"]
__version__ = "0.1.0"
