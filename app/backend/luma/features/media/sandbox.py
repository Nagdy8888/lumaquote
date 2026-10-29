"""Host adapter for the fixed, offline Docker parser; no caller-chosen command is accepted."""

import json
import subprocess
import tempfile
import threading
from pathlib import Path
from uuid import uuid4

from luma.core.errors import DomainError

LIMITS = {"pdf": 20 * 1024 * 1024, "image": 5 * 1024 * 1024, "audio": 10 * 1024 * 1024}


def bounded_output(command: list[str]) -> bytes:
    """Bound host-side stdout to 4 MB and wall time to 50 seconds even if an untrusted parser streams indefinitely."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    ready = threading.Event()
    output = []

    def read_result():
        """Read one bounded result from the child pipe; never accumulate untrusted stderr or an unlimited stream."""
        output.append(process.stdout.read(4 * 1024 * 1024 + 1))
        ready.set()

    reader = threading.Thread(target=read_result, daemon=True)
    reader.start()
    try:
        if not ready.wait(50):
            raise subprocess.TimeoutExpired(command, 50)
        if len(output[0]) > 4 * 1024 * 1024:
            raise DomainError("File-processing output exceeded its safe limit.", 422)
        if process.wait(timeout=3) != 0:
            raise DomainError(
                "The file could not be safely processed. Send text or another supported file.", 422
            )
        return output[0]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)
        reader.join(timeout=1)
        process.stdout.close()


def process_file(kind: str, data: bytes) -> tuple[dict, bytes | None]:
    """Parse bounded bytes in an ephemeral constrained container; return validated metadata and optional normalized bytes."""
    if kind not in LIMITS or not data or len(data) > LIMITS[kind]:
        raise DomainError("This file is empty, unsupported, or exceeds its size limit.", 422)
    name = "luma-media-" + str(uuid4())
    with tempfile.TemporaryDirectory(prefix="luma-media-") as temporary:
        root = Path(temporary)
        source = root / "file"
        output = root / "output"
        source.write_bytes(data)
        output.mkdir()
        command = [
            "docker",
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--memory",
            "256m",
            "--memory-swap",
            "256m",
            "--cpus",
            "1",
            "--pids-limit",
            "64",
            "--ulimit",
            "fsize=16777216:16777216",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=32m",
            "--mount",
            f"type=bind,source={source},target=/input/file,readonly",
            "--mount",
            f"type=bind,source={output},target=/output",
            "lumaquote-media:local",
            kind,
        ]
        try:
            metadata = json.loads(bounded_output(command))
            if not isinstance(metadata, dict) or metadata.get("kind") != kind:
                raise DomainError("Invalid file-processing result.", 422)
            normalized = None
            if kind in ("audio", "image"):
                expected = "normalized.wav" if kind == "audio" else "normalized.jpg"
                if metadata.get("output") != expected:
                    raise DomainError("Invalid normalized file reference.", 422)
                target = output / expected
                if target.is_symlink() or not target.is_file() or target.stat().st_size > 8 * 1024 * 1024:
                    raise DomainError("Normalized file exceeds its allowed boundary.", 422)
                normalized = target.read_bytes()
            return metadata, normalized
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            raise DomainError(
                "File processing is unavailable. A staff member can continue with text.", 503
            ) from None
        finally:
            # Killing the CLI alone does not stop a timed-out container.
            try:
                subprocess.run(
                    ["docker", "rm", "-f", name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (subprocess.TimeoutExpired, OSError):
                # Preserve the original safe rejection if Docker itself is unavailable.
                pass
