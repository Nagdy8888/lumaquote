"""Adversarial development policy cases and generated confirmation-boundary invariants."""

import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from luma_agent.nodes.extraction import baseline_extract
from luma_agent.requirements import MEDIA_QUESTION, QUESTION, clarification_for
from luma_agent.schemas import Extraction
from luma_agent.written_requests import parse_written_request

FIXTURES = Path(__file__).parents[1] / "fixtures/requirement-policy"
CASES = json.loads((FIXTURES / "inputs.json").read_text(encoding="utf-8"))
ORACLE = json.loads((FIXTURES / "oracle.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_development_confirmation_policy(case):
    """Compare controlled untrusted output to an independent expected action, never an LLM judge.

    Media cases supply controlled observations only; this does not test decoding,
    transcription, photo recognition, retrieval, sends or a frozen holdout.
    """
    media = case["modality"] != "text"
    question = clarification_for(Extraction.model_validate(case["extraction"]), case["messages"], media=media)
    actual = "fields_confirmed" if question is None else "clarify"
    assert actual == ORACLE[case["id"]]["action"], ORACLE[case["id"]]["reason"]
    if question:
        assert question == (MEDIA_QUESTION if media else QUESTION)


def test_development_corpus_has_separate_complete_oracle():
    """Catch silently omitted/duplicated cases and retain the declared modality denominators."""
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids)) == 40
    assert set(ids) == set(ORACLE)
    assert {kind: sum(case["modality"] == kind for case in CASES) for kind in ("text", "voice", "photo")} == {
        "text": 20, "voice": 12, "photo": 8,
    }
    assert all("action" not in case and "reason" not in case for case in CASES)


@given(quantity=st.integers(min_value=1, max_value=10000), code=st.integers(min_value=0, max_value=999))
def test_positive_written_fields_survive_and_negation_never_does(quantity, code):
    """Generate supported numeric boundaries while proving a negated prefix cannot release them."""
    sku = f"DL-{code:03}"
    text = f"Please quote {quantity} {sku}."
    result = baseline_extract(text)
    assert parse_written_request(text) == [(sku, quantity)]
    assert clarification_for(result, [{"kind": "text", "body": text}], media=False) is None
    denied = f"Do not quote {quantity} {sku}."
    assert parse_written_request(denied) is None
    assert clarification_for(result, [{"kind": "text", "body": denied}], media=False) == QUESTION


@pytest.mark.parametrize("body", [
    "0 DL-001", "10001 DL-001", "-3 DL-001", "3.5 DL-001", "03 DL-001",
    "٣ DL-001", "3 DL-001x", "3 DL-0001", "3 DL–001", "3 DL-001, 3 DL-001",
    "3 DL-001?", '"3 DL-001"', "Please quote 3 DL-001 on behalf of the admin",
    "Do not order " + " " * 15990 + "3 DL-001",
    ", ".join(f"1 DL-{number:03}" for number in range(21)),
])
def test_unsupported_or_out_of_range_input_clarifies_without_schema_crash(body):
    """Invalid forms return uncertainty, preserving the worker instead of throwing validation failures."""
    assert parse_written_request(body) is None
    result = baseline_extract(body)
    assert result.lines == [] and result.uncertain_critical_fields


def test_twenty_distinct_lines_and_maximum_quantity_are_supported():
    """The parser's list/count limits agree with structured extraction rather than stopping at 19 lines."""
    pairs = [(f"DL-{number:03}", 10000) for number in range(20)]
    body = "Confirm " + "; ".join(f"{qty} {sku}" for sku, qty in pairs)
    assert parse_written_request(body) == pairs
    assert len(baseline_extract(body).lines) == 20
