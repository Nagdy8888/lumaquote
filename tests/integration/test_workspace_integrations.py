"""Workspace integration status reflects current GAS configuration without leaking secrets."""

import pytest
from luma.core.config import settings


@pytest.mark.parametrize("mapped", [False, True])
def test_workspace_reports_only_complete_tenant_mapped_gas_configuration(environment, monkeypatch, mapped):
    """Removing backend OAuth must not break workspace reads or imply live synchronization verification."""
    env = environment
    monkeypatch.setenv("GOOGLE_SHEET_ID", "synthetic-sheet")
    monkeypatch.setenv("GOOGLE_CALLBACK_SECRET", "synthetic-callback-secret")
    monkeypatch.setenv("GOOGLE_COMPANY_ID", str(env["company"]) if mapped else "")
    settings.cache_clear()
    response = env["api"].get("/api/workspace", headers=env["headers"])
    assert response.status_code == 200
    assert response.json()["integrations"]["google"] == (
        "configured_unverified" if mapped else "not_connected"
    )
    assert "synthetic-callback-secret" not in response.text
    settings.cache_clear()
