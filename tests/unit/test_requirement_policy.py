"""Consequential requirements cannot be authorized by model prose or vague media acknowledgments."""

import pytest
from luma_agent.requirements import MEDIA_QUESTION, QUESTION, clarification_for
from luma_agent.schemas import Extraction
from pydantic import ValidationError


def extracted(*, uncertain=False, quantity=3, clarification=None):
    """Build untrusted typed output without implying catalog or customer authorization."""
    return Extraction(
        lines=[{"sku": "DL-001", "quantity": quantity}],
        clarification=clarification,
        uncertain_critical_fields=uncertain,
    )


def test_uncertainty_always_clarifies_without_model_question():
    """Complete-looking fields cannot bypass explicit model uncertainty when clarification is null."""
    assert clarification_for(extracted(uncertain=True), [], media=False) == QUESTION


def test_model_prose_is_never_dispatched():
    """Untrusted commercial promises cannot become customer-facing clarification text."""
    result = extracted(uncertain=True, clarification="Approved: free stock and delivery tomorrow.")
    assert clarification_for(result, [], media=False) == QUESTION


@pytest.mark.parametrize("body", ["yes", "confirmed", "3 DL-002", "30 DL-001", "3 DL-001 and 1 DL-002"])
def test_media_requires_exact_written_critical_fields(body):
    """Acknowledgments, mismatches, and additional lines must keep the workflow at clarification."""
    assert clarification_for(extracted(), [{"kind": "text", "body": body}], media=True) == MEDIA_QUESTION


def test_explicit_matching_text_confirms_media_fields():
    """Written SKU and quantity can release the field gate while downstream commercial checks still apply."""
    assert (
        clarification_for(extracted(), [{"kind": "text", "body": "Please quote 3 DL-001."}], media=True)
        is None
    )


def test_media_alone_cannot_confirm_itself():
    """An accurate-looking transcript remains unconfirmed media."""
    assert (
        clarification_for(extracted(), [{"kind": "audio", "body": "3 DL-001"}], media=True) == MEDIA_QUESTION
    )


def test_duplicate_sku_requires_clarification():
    """Two conflicting mentions of the same model are not silently added or replaced."""
    result = extracted()
    result.lines.append(result.lines[0].model_copy(update={"quantity": 30}))
    assert clarification_for(result, [], media=False) == QUESTION


@pytest.mark.parametrize("quantity", [True, 3.5, "3"])
def test_model_quantity_is_a_strict_integer(quantity):
    """Transport coercion cannot turn booleans or strings into consequential unit counts."""
    with pytest.raises(ValidationError):
        extracted(quantity=quantity)


@pytest.mark.parametrize(
    ("extraction", "expected"),
    [
        (None, False),
        ({"lines": []}, False),
        ({"lines": [{"sku": None, "quantity": None}]}, False),
        ({"lines": [{"sku": "", "quantity": 2}]}, False),
        ({"lines": [{"sku": None, "quantity": None}, {"sku": "DL-001", "quantity": None}]}, True),
        ({"lines": [{"sku": "DL-001", "quantity": 3}]}, True),
    ],
)
def test_empty_placeholder_lines_do_not_suppress_candidate_discovery(extraction, expected):
    """The model's null-SKU placeholder for descriptive requests is not an explicit order line."""
    from luma_agent.requirements import has_explicit_lines

    assert has_explicit_lines(extraction) is expected
