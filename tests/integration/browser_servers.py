"""Start isolated native API and Vite servers for a fixture tenant and run one Playwright review script.

Used by the whole-app UI review, the scene and page reviews, and any other review that needs a signed-in
browser. Both servers bind unused loopback ports, log under `.local/`, and are always stopped. The scenario
file holds the fixture user's throwaway credentials and is deleted afterwards.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from test_browser_workflow import available_port, wait_for_server

ROOT = Path(__file__).resolve().parents[2]


def run_review(env, script: str, name: str, report_path: Path, extra: dict | None = None, timeout: int = 150):
    """Run `tests/browser/<script>` against fresh servers and return its JSON report.

    Inputs: the integration `environment` fixture, the script file name, a log label and the path the
    script writes its report to. Side effects: spawns uvicorn and Vite, writes `.local/<name>-*.log`,
    creates and removes a scenario file. Errors: fails the calling test if a server does not start or
    the script exits nonzero (its stderr is shown, truncated).
    """
    api_port, ui_port = available_port(), available_port()
    (ROOT / ".local").mkdir(exist_ok=True)
    scenario = ROOT / ".local" / f"{name}-{env['company']}-scenario.json"
    scenario.write_text(
        json.dumps(
            {
                "url": f"http://127.0.0.1:{ui_port}",
                "email": env["email"],
                "password": env["password"],
                "report": str(report_path),
                **(extra or {}),
            }
        ),
        encoding="utf-8",
    )
    child = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join([str(ROOT / "app/backend"), str(ROOT / "app/agents")]),
        "LUMA_API_PROXY_TARGET": f"http://127.0.0.1:{api_port}",
    }
    servers = []
    try:
        with (
            (ROOT / f".local/{name}-api.log").open("w") as api_log,
            (ROOT / f".local/{name}-ui.log").open("w") as ui_log,
        ):
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
                env=child,
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
                env=child,
                stdout=ui_log,
                stderr=subprocess.STDOUT,
            )
            servers.append(ui)
            wait_for_server(f"http://127.0.0.1:{api_port}/api/health", api)
            wait_for_server(f"http://127.0.0.1:{ui_port}", ui)
            result = subprocess.run(
                ["node", str(ROOT / "tests/browser" / script), str(scenario)],
                cwd=ROOT,
                env=child,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        assert result.returncode == 0, result.stderr[:2500]
        return json.loads(report_path.read_text(encoding="utf-8"))
    finally:
        for server in reversed(servers):
            if server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
        scenario.unlink(missing_ok=True)
