from decimal import Decimal

from luma.core.config import settings
from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.conversations.repository import conversation
from openai import OpenAI

from ..brain import (
    INSTRUCTIONS,
    catalog_context,
    is_yes,
    known_skus,
    model_input,
    restatement,
    safe_reply,
    transcript,
    unknown_reply,
    valid_lines,
)
from ..budget import reserve
from ..lease import assert_job
from ..observability import masked_or_off, model_call, set_outputs, set_usage
from ..requirements import MEDIA_QUESTION, QUESTION, clarification_for
from ..schemas import Extraction, RequestedLine
from ..written_requests import parse_written_request


def baseline_extract(text):
    """Read only complete positive written orders with the shared bounded grammar.

    Unsupported prose, negation, pack units and duplicate/oversized lines produce an
    empty uncertain result rather than substring matches or validation crashes.
    This is an explicit offline baseline, not live model reasoning or approval.
    """
    matches = parse_written_request(text)
    return Extraction(
        lines=[RequestedLine(sku=sku, quantity=quantity) for sku, quantity in matches or []],
        clarification=None if matches else "Which product model (SKU) and quantity do you need?",
        uncertain_critical_fields=not bool(matches),
    )


def extract(state):
    """Read the latest authorized customer turn and decide: confirmed order, restatement or reply.

    Paid AI off: the deterministic whole-message grammar is the only reader (decision D20).
    Paid AI on (decision D45): a plain YES that directly answers the previous restatement
    confirms exactly the restated pairs without any model call. Otherwise the model reads the
    recent conversation plus a specification-only catalog listing. A written order that the
    grammar parses and the model agrees with is confirmed; any other complete order (the
    customer's own written pairs win over the model's reading) is restated for a YES; else the
    filtered model reply or a fixed question is sent. Model output never confirms by itself.
    Lease/owner checks and the paid reservation precede provider work; usage settlement and
    uncertain failures keep their separate transaction boundary. Oversized bodies never reach
    the model. Returns the per-turn state, always resetting `pending_order` and `brain_reply`.
    """
    config = settings()
    pending = [tuple(pair) for pair in state.get("pending_order") or []]
    with database(worker=True) as conn:
        assert_job(conn, state)
        current = conversation(conn, state["company_id"], state["conversation_id"])
        if current["owner"] != "agent":
            raise DomainError("Staff takeover has paused the agent.")
        messages = conn.execute(
            "select id,body,kind from luma.messages where conversation_id=%s and actor='customer' order by created_at desc,id desc limit 12",
            (state["conversation_id"],),
        ).fetchall()
        text = messages[0]["body"] if messages else ""
        media = any(m["kind"] in ("audio", "image") for m in messages)
        turn = {
            "customer_message_id": str(messages[0]["id"]) if messages else "",
            "observed_version": current["version"],
            "pending_order": [],
            "pending_after": None,
            "brain_reply": False,
        }
        if len(text) > 16000:
            # Never discard a negation/condition before checking the full request.
            return {
                **turn,
                "extraction": baseline_extract("").model_dump(),
                "clarification": clarification_for(baseline_extract(""), messages, media=media),
            }
        if (
            config.enable_paid_ai
            and pending
            and len(messages) > 1
            and messages[0]["kind"] == "text"
            and str(messages[1]["id"]) == state.get("pending_after")
            and is_yes(text)
        ):
            # Deterministic consent: the YES answers exactly the restated order, no model call.
            lines = [RequestedLine(sku=sku, quantity=quantity) for sku, quantity in pending]
            confirmed = Extraction(lines=lines, clarification=None, uncertain_critical_fields=False)
            return {**turn, "extraction": confirmed.model_dump(), "clarification": None}
        if config.enable_paid_ai:
            if config.openai_model != "gpt-6-luna":
                raise DomainError(
                    "This model has no verified estimated-allowance policy. Keep paid AI disabled.", 503
                )
            if not config.openai_api_key.get_secret_value():
                raise DomainError("OpenAI is enabled but its key is missing.", 503)
            history = transcript(conn, state["company_id"], state["conversation_id"])
            prompt = model_input(history, catalog_context(conn, state["company_id"], text, history))
            reserve(conn, state["company_id"], state["job_id"])
    if not config.enable_paid_ai:
        result = baseline_extract(text)
        return {
            **turn,
            "extraction": result.model_dump(),
            "clarification": clarification_for(result, messages, media=media),
        }
    try:
        # Full (masked) trace only inside the worker's job trace; otherwise off (observability.py).
        with (
            masked_or_off(),
            model_call(
                "openai.responses.extraction",
                config.openai_model,
                {"instructions": INSTRUCTIONS, "input": prompt},
            ) as call,
        ):
            response = OpenAI(
                api_key=config.openai_api_key.get_secret_value(), timeout=45, max_retries=0
            ).responses.parse(
                model=config.openai_model,
                service_tier="default",
                reasoning={"effort": "none"},
                store=False,
                max_output_tokens=1600,
                instructions=INSTRUCTIONS,
                input=prompt,
                text_format=Extraction,
            )
            set_usage(
                call,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                input_usd_per_million=0.10,
                output_usd_per_million=0.50,
            )
            set_outputs(
                call,
                {
                    "parsed": response.output_parsed.model_dump() if response.output_parsed else None,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                },
            )
        result = response.output_parsed
        if result is None:
            raise DomainError("The model did not return usable requirements.")
        # Conservative token-derived estimate; never represented as provider billing.
        estimate = (
            Decimal(response.usage.input_tokens) * Decimal("0.10")
            + Decimal(response.usage.output_tokens) * Decimal("0.50")
        ) / Decimal(1000000)
        written = parse_written_request(text) if messages and messages[0]["kind"] == "text" else None
        reading = valid_lines(result)
        proposal = written or reading
        with database(worker=True) as conn:
            conn.execute(
                "update luma.usage set status='settled',estimated=%s where job_id=%s and operation='primary'",
                (estimate, state["job_id"]),
            )
            known = known_skus(conn, state["company_id"], [sku for sku, _ in proposal or []])
    except Exception:
        with database(worker=True) as conn:
            conn.execute(
                "update luma.usage set status='unknown' where job_id=%s and operation='primary'",
                (state["job_id"],),
            )
        raise
    if written and reading and sorted(written) == sorted(reading):
        lines = [RequestedLine(sku=sku, quantity=quantity) for sku, quantity in written]
        confirmed = Extraction(lines=lines, clarification=None, uncertain_critical_fields=False)
        return {**turn, "extraction": confirmed.model_dump(), "clarification": None}
    reply = safe_reply(result.clarification)
    unknown = [sku for sku, _ in proposal or [] if sku not in known]
    if proposal and unknown:
        question = unknown_reply(unknown)
    elif proposal:
        question = f"{reply}\n\n{restatement(proposal)}" if reply else restatement(proposal)
        turn["pending_order"] = [list(pair) for pair in proposal]
        turn["pending_after"] = turn["customer_message_id"]
    else:
        question = reply or (MEDIA_QUESTION if media else QUESTION)
    turn["brain_reply"] = True
    empty = Extraction(lines=[], clarification=None, uncertain_critical_fields=True)
    return {**turn, "extraction": empty.model_dump(), "clarification": question}
