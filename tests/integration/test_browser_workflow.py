"""Actual native UI/API/worker browser slice with an isolated Auth/database/Storage fixture."""

import io
import json
import os
import socket
import subprocess
import sys
import time

import httpx
import psycopg
import pytest
from luma.core.config import ROOT
from luma.core.storage import put_file
from reportlab.pdfgen.canvas import Canvas


def available_port() -> int:
    """Select an unused loopback test port; strict server startup fails visibly if another process wins the bind race."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(url: str, process: subprocess.Popen):
    """Wait a bounded period for the owned native server, failing if it exits rather than masking startup errors."""
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail("An isolated native test server exited before becoming ready.")
        try:
            if httpx.get(url, timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    pytest.fail("An isolated native test server did not become ready before the deadline.")


@pytest.mark.browser
def test_complete_native_browser_workflow(environment):
    """Verify the real staff workflow, stale-edit preservation, exact revision, private documents, and persisted local delivery."""
    env = environment
    api_port = available_port()
    ui_port = available_port()
    scenario = ROOT / ".local" / f"browser-{env['company']}.json"
    scenario.parent.mkdir(exist_ok=True)
    scenario.write_text(
        json.dumps(
            {
                "url": f"http://127.0.0.1:{ui_port}",
                "email": env["email"],
                "password": env["password"],
                "product_id": str(env["products"][0]),
                "company_id": str(env["company"]),
            }
        ),
        encoding="utf-8",
    )
    original = io.BytesIO()
    catalog = Canvas(original)
    catalog.drawString(40, 750, "Synthetic DL-001, 18W, 1800 lm, 4000K. Private original evidence.")
    catalog.save()
    source_path = f"{env['company']}/catalogs/test.pdf"
    put_file(source_path, original.getvalue(), "application/pdf")
    env["files"].append(source_path)
    child_environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(ROOT / "app/backend"), str(ROOT / "app/agents")]),
        "LUMA_API_PROXY_TARGET": f"http://127.0.0.1:{api_port}",
    }
    servers = []
    with (
        (ROOT / ".local/browser-api.log").open("w") as api_log,
        (ROOT / ".local/browser-ui.log").open("w") as ui_log,
    ):
        try:
            api = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "luma.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                cwd=ROOT,
                env=child_environment,
                stdout=api_log,
                stderr=subprocess.STDOUT,
            )
            servers.append(api)
            ui = subprocess.Popen(
                [
                    "node",
                    str(ROOT / "node_modules/vite/bin/vite.js"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(ui_port),
                    "--strictPort",
                ],
                cwd=ROOT / "app/frontend",
                env=child_environment,
                stdout=ui_log,
                stderr=subprocess.STDOUT,
            )
            servers.append(ui)
            wait_for_server(f"http://127.0.0.1:{api_port}/api/health", api)
            wait_for_server(f"http://127.0.0.1:{ui_port}", ui)
            result = subprocess.run(
                ["node", str(ROOT / "tests/browser/manual-workflow.cjs"), str(scenario)],
                cwd=ROOT,
                env=child_environment,
                capture_output=True,
                text=True,
                timeout=300 if os.environ.get("LUMA_RECORD_DIR") else 90,
            )
            assert result.returncode == 0, result.stderr[:2500]
            report = json.loads(result.stdout)
            with psycopg.connect(env["dsn"]) as conn:
                for qid in report["canonical_pdf_ids"]:
                    assert conn.execute(
                        "select 1 from luma.quotes where id=%s and company_id=%s", (qid, env["company"])
                    ).fetchone()
                    env["files"].append(f"{env['company']}/quotes/{qid}.pdf")
                assert (
                    conn.execute(
                        "select count(*) from luma.outbox where company_id=%s and kind='quotation' and status='local_delivered'",
                        (env["company"],),
                    ).fetchone()[0]
                    == 1
                )
            assert len(report["checks"]) == 13
            # A new native API process must read the same canonical quotation
            # and delivery after the original application process has stopped.
            api.terminate()
            api.wait(timeout=5)
            replacement = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "luma.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                cwd=ROOT,
                env=child_environment,
                stdout=api_log,
                stderr=subprocess.STDOUT,
            )
            servers.append(replacement)
            wait_for_server(f"http://127.0.0.1:{api_port}/api/health", replacement)
            persisted = httpx.get(
                f"http://127.0.0.1:{api_port}/api/conversations/{report['conversation_id']}",
                headers=env["headers"],
                timeout=5,
            )
            assert persisted.status_code == 200
            assert persisted.json()["quote"]["revision"] == 2
            assert persisted.json()["quote"]["content"]["total"] == "129.40"
            assert any(
                item["kind"] == "quotation" and item["status"] == "local_delivered"
                for item in persisted.json()["delivery"]
            )
        finally:
            for server in reversed(servers):
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait(timeout=5)
            scenario.unlink(missing_ok=True)
