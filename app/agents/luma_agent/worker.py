"""Native worker entry point; infrastructure stays in local Supabase."""

import argparse
import logging
import time

from luma.core.errors import DomainError

from .observability import trace_outcome
from .runtime.conversations import process_conversation
from .runtime.delivery import deliver_one
from .runtime.jobs import claim_job, finish_job

logger = logging.getLogger("luma.worker")


def tick():
    """Run one claimed graph job and one dispatch, recording safe failure codes without provider payloads."""
    job = claim_job()
    if job:
        outcome = "done"
        try:
            if job["kind"] != "agent":
                raise DomainError("This integration job is not enabled yet.")
            process_conversation(job)
            finish_job(job, "done")
        except Exception as error:
            outcome = "blocked" if isinstance(error, DomainError) else "failed"
            finish_job(job, outcome, type(error).__name__)
            logger.warning("Job %s: %s", str(job["id"]), type(error).__name__)
        try:
            trace_outcome(job, outcome)
        except Exception as error:
            logger.warning("Trace export unavailable: %s", type(error).__name__)
    return bool(job) or deliver_one()


def main():
    """Poll durable jobs until interrupted, or perform one bounded tick for tests and local diagnostics."""
    parser = argparse.ArgumentParser(description="LumaQuote durable worker")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    while True:
        tick()
        if args.once:
            return
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
