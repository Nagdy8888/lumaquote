"""Pure safety helpers of the paid brain (D45): YES detection, reply filter, order validation, restatement."""

import pytest
from luma_agent.brain import is_yes, restatement, safe_reply, valid_lines
from luma_agent.schemas import Extraction


@pytest.mark.parametrize("text", ["yes", "YES", "Yes please", "ok", "Confirm.", "yes, confirmed!", "نعم", "تمام"])
def test_plain_agreement_is_yes(text):
    """Whole-message agreement words count as YES."""
    assert is_yes(text)


@pytest.mark.parametrize("text", ["yes but 10", "no", "yes 5 DL-001", "not yes", "maybe", "", "yesss"])
def test_anything_more_than_agreement_is_not_yes(text):
    """Extra words, negation or changes never count as YES."""
    assert not is_yes(text)


@pytest.mark.parametrize("text", [
    "It costs $5.", "Only 30 EGP.", "Save 10 %.", "Approved for you.", "Visit http://x.invalid",
    "We guarantee delivery.", "Sent without review.", "x" * 701, "", None,
])
def test_unsafe_or_empty_replies_are_dropped(text):
    """Money, percentages, links, guarantees, approval claims and oversize replies return None."""
    assert safe_reply(text) is None


def test_plain_reply_passes_trimmed():
    """An ordinary product answer is kept."""
    assert safe_reply("  DL-001 is an 18W downlight. How many do you need?  ") == (
        "DL-001 is an 18W downlight. How many do you need?"
    )


def make(lines, uncertain=False):
    """Build a typed model output from (sku, quantity) pairs."""
    return Extraction(
        lines=[{"sku": sku, "quantity": quantity} for sku, quantity in lines],
        clarification=None,
        uncertain_critical_fields=uncertain,
    )


def test_valid_lines_normalize_case():
    """Lower-case model SKUs are normalized; pairs keep their order."""
    assert valid_lines(make([("dl-001", 5), ("DL-002", 2)])) == [("DL-001", 5), ("DL-002", 2)]


@pytest.mark.parametrize("lines,uncertain", [
    ([], False),
    ([("DL-001", 5)], True),
    ([("DL001", 5)], False),
    ([("DL-001", None)], False),
    ([(None, 5)], False),
    ([("DL-001", 5), ("dl-001", 2)], False),
])
def test_unusable_model_orders_are_rejected(lines, uncertain):
    """Uncertain, malformed, missing or duplicate lines give None."""
    assert valid_lines(make(lines, uncertain)) is None


def test_restatement_is_built_from_pairs_only():
    """The confirmation question names exactly the validated pairs."""
    assert restatement([("DL-001", 5), ("DL-002", 2)]) == (
        "To confirm, your order is: 5 x DL-001, 2 x DL-002. Reply YES to confirm, or send the corrected order."
    )
