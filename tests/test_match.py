"""matches_entity -- every case here is a REAL collision found in
production (7th Sense, a company-intelligence SaaS), not invented. See
the README for the full story of each one.
"""
from entitygate.match import matches_entity


def test_generic_industry_word_does_not_bridge_two_companies():
    """Real bug: naive "any token matches" accepted "apollohospitals" as
    Kauvery Hospital's handle, because both names contain "hospital(s)".
    Anchoring on the brand token (not a shared generic word) rejects it."""
    assert matches_entity("apollohospitals", "Kauvery Hospital") is False
    assert matches_entity("apollohospitals", "Apollo Hospitals") is True


def test_short_brand_anchor_needs_corroboration():
    """A short, commonly-shared first token ("Sri", "Max") must not carry
    a match alone -- it needs a second real token from the entity name."""
    assert matches_entity("srivenkateswara", "Sri Krishna Sweets") is False
    assert matches_entity("apollohealthcare", "Max Healthcare") is False


def test_distinctive_anchor_stands_alone_against_a_real_slug():
    """Real observed case: Prashanth Hospitals' actual LinkedIn slug is
    "company/prashanth-multispeciality" -- brand present, "hospitals"
    absent. Requiring every name-token to match would throw away this
    genuinely correct identifier."""
    assert matches_entity("company/prashanth-multispeciality", "Prashanth Hospitals") is True


def test_name_collision_across_unrelated_industries():
    """Real bug: a hotel named "Sundaram Residency" collided with an
    unrelated finance company "Sundaram Finance" purely on the shared
    brand word "Sundaram" -- this is the category this specific test
    does NOT protect against on its own (both share the full anchor
    token "sundaram"); see the README's "known limitation" section for
    why this is a disclosed, not hidden, gap in the anchor-matching
    approach alone."""
    # Documents the real limitation rather than asserting a false claim:
    # anchor-matching alone cannot distinguish two real entities that
    # legitimately share the same distinctive brand word.
    assert matches_entity("sundaramfinance", "Sundaram Residency") is True  # known false positive, see README


def test_longer_official_name_than_handle_still_matches():
    assert matches_entity("prashanthhospitals", "Prashanth Super Speciality Hospital") is True


def test_cross_platform_fabrication_is_not_caught_by_this_function_alone():
    """matches_entity only checks entity ownership, not whether the
    candidate was ever actually stated for THIS platform -- that's
    verify_claim's job (the verbatim + shape gates), not this function's.
    Documented here so the split of responsibility is explicit."""
    assert matches_entity("apollohospitals", "Apollo Hospitals") is True


def test_entity_with_no_usable_tokens_fails_closed():
    assert matches_entity("anything", "") is False
    assert matches_entity("anything", "Ltd Inc Pvt") is False  # only stopwords
