"""verify_claim -- the combined shape + verbatim + entity-match gate."""
from entitygate.verify import verify_claim


def _instagram_shape(candidate: str) -> bool:
    return "/p/" not in candidate and "/reel/" not in candidate


def test_the_original_real_bug_this_library_exists_for():
    """Real captured case (see README): an AI Overview cited an unrelated
    third party's Instagram handle ("timedical1") as a source inside a
    paragraph about Prashanth Hospitals' market trends. The candidate is
    REAL (verbatim in the source) and well-shaped -- a generic
    groundedness/fabrication checker would accept it. Only the entity
    match gate catches that it isn't Prashanth's."""
    source_text = "Instagram\n\xb7timedical1\n +1\nKey Market Trends"
    result = verify_claim("timedical1", "Prashanth Hospitals", source_text)
    assert result.verified is False
    assert result.reason == "no_entity_match"


def test_real_correct_handle_is_accepted():
    source_text = "Follow us on Instagram: instagram.com/prashanthhospitals_velachery"
    result = verify_claim(
        "instagram.com/prashanthhospitals_velachery", "Prashanth Hospitals", source_text
    )
    assert result.verified is True
    assert result.reason == "ok"


def test_fabricated_candidate_rejected_before_entity_check_even_runs():
    """A candidate the model invented -- not actually present in the
    source -- is rejected at the verbatim gate, the same basic check
    every fabrication detector already does. entitygate doesn't claim
    novelty here; it's a necessary precondition for the entity-match gate
    to mean anything."""
    result = verify_claim("totally_made_up_handle", "Prashanth Hospitals", "Prashanth Hospitals is a Chennai hospital.")
    assert result.verified is False
    assert result.reason == "not_verbatim_in_source"


def test_wrong_shape_rejected_before_entity_check_even_runs():
    source_text = "Prashanth Hospitals: instagram.com/p/DXyz123"
    result = verify_claim("instagram.com/p/DXyz123", "Prashanth Hospitals", source_text, shape=_instagram_shape)
    assert result.verified is False
    assert result.reason == "no_shape_match"


def test_real_but_wrong_entity_with_correct_shape_still_rejected():
    """The core demonstration: shape is fine, verbatim is fine, and it's
    STILL rejected -- because shape+verbatim alone (what generic tools
    check) is not enough."""
    source_text = "Apollo Hospitals official page: instagram.com/apollohospitals"
    result = verify_claim(
        "instagram.com/apollohospitals", "Kauvery Hospital", source_text, shape=_instagram_shape
    )
    assert result.verified is False
    assert result.reason == "no_entity_match"
