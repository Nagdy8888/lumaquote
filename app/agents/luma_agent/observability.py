from datetime import UTC, datetime

from langsmith import Client
from luma.core.config import settings


def trace_outcome(job, outcome):
    """Export only opaque job identity and outcome to the configured LangSmith project; automatic raw tracing stays disabled."""
    config = settings()
    if not config.langsmith_tracing or not config.langsmith_api_key.get_secret_value():
        return
    # Automatic graph/model tracing is disabled at invocation. This explicit root
    # trace has an allowlist of opaque identifiers and statuses; no raw input,
    # transcript, phone, document, URL, prompt, or nested tool output is exported.
    client = Client(api_key=config.langsmith_api_key.get_secret_value(), api_url=config.langsmith_endpoint)
    client.create_run(
        name="quotation.workflow",
        run_type="chain",
        project_name=config.langsmith_project,
        inputs={"job_id": str(job["id"])},
        outputs={"status": outcome},
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC),
    )
