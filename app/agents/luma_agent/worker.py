"""Native worker entry point; infrastructure stays in local Supabase."""

import argparse
import logging
import threading
import time

from luma.core.database import database
from luma.core.errors import DomainError
from luma.features.inventory import ledger
from luma.features.messaging import provider
from luma.features.messaging.inbound import process_next as process_inbox
from luma.features.messaging.telegram_ingress import poll_once

from .observability import finish, flush, job_trace
from .runtime.audio import process_audio
from .runtime.conversations import process_conversation
from .runtime.delivery import deliver_one
from .runtime.jobs import claim_job, finish_job
from .runtime.media import process_media

logger = logging.getLogger("luma.worker")


def reconcile_stock() -> int:
    """Release stock reservations that no longer protect a live quotation; return how many quotations were released.

    Runs `ledger.reconcile` (expired quotes, dead deliveries, quotes that are no longer approved;
    decision D49) in its own short worker transaction, so a failure here never touches a job or
    a dispatch. Any error is logged as its class name only and swallowed: the next tick retries
    and the loop never stops. Returns 0 after a failure.
    """
    try:
        with database(worker=True) as conn:
            conn.execute("set local statement_timeout='10s'")
            result = ledger.reconcile(conn)
    except Exception as error:
        logger.warning("Stock reconcile: %s", type(error).__name__)
        return 0
    if result["released"]:
        logger.info("Stock reconcile: released %s, expired %s", result["released"], result["expired"])
    return result["released"]


def tick():
    """Run one claimed graph job, one dispatch, one inbound event and one stock reconcile.

    Each job runs inside a masked LangSmith root trace when tracing is enabled
    (`observability.job_trace`, decision D24); its graph steps and model calls nest
    under it, and the root records the outcome and error class. Logs keep safe failure
    codes only. Trace export never changes the job outcome. The stock reconcile
    (`reconcile_stock`) runs last, after the dispatch and inbound work of the tick.
    """
    job = claim_job()
    if job:
        with job_trace(job) as run:
            outcome, failure = "done", None
            try:
                if job["kind"] == "agent":
                    process_conversation(job)
                elif job["kind"] == "transcribe":
                    process_audio(job)
                elif job["kind"] == "read_photo":
                    process_media(job, "image")
                else:
                    raise DomainError("This integration job is not enabled yet.")
                finish_job(job, "done")
            except Exception as error:
                outcome = "blocked" if isinstance(error, DomainError) else "failed"
                failure = type(error).__name__
                finish_job(job, outcome, failure)
                logger.warning("Job %s: %s", str(job["id"]), failure)
            finish(run, outcome, failure)
        flush()
    dispatched = deliver_one()
    received = process_inbox()
    released = reconcile_stock()
    return bool(job) or dispatched or received or bool(released)


def poll_telegram(stop: threading.Event) -> None:
    """Long-poll Telegram until `stop` is set, storing updates in the inbox before confirming them (D44).

    Runs on its own daemon thread so a 25-second long poll never delays jobs or dispatch. A
    storage failure keeps the previous offset (nothing is confirmed) and waits five seconds;
    only the exception class is logged, never update content or the token-bearing URL.
    """
    offset = None
    while not stop.is_set():
        try:
            offset = poll_once(offset)
        except Exception as error:
            logger.warning("Telegram poll: %s", type(error).__name__)
            stop.wait(5)


def main():
    """Poll durable jobs until interrupted, or perform one bounded tick for tests and local diagnostics.

    When a Telegram bot is configured (and not in `--once` mode) a poller thread feeds the
    inbox; the `httpx` and `httpx2` request loggers stay at WARNING because Bot API URLs contain the token.
    """
    parser = argparse.ArgumentParser(description="LumaQuote durable worker")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for name in ("httpx", "httpx2"):  # openai 3.x sends through httpx2, which logs request URLs at INFO
        logging.getLogger(name).setLevel(logging.WARNING)
    if not args.once and provider.ready("telegram"):
        threading.Thread(target=poll_telegram, args=(threading.Event(),), daemon=True, name="telegram").start()
        logger.info("Telegram polling started")
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
