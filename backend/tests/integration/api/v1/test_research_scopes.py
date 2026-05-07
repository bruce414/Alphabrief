from __future__ import annotations

import pytest

from app.core.enums import (
    AnalysisIntent,
    CompletionStrategy,
    CoverageMode,
    ResearchMode,
    ResearchScope,
)


@pytest.mark.asyncio
async def test_get_research_scopes_returns_expected_payload(client):
    r = await client.get("/api/v1/research-scopes")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data == {
        "researchScopes": [s.value for s in ResearchScope],
        "researchModes": [s.value for s in ResearchMode],
        "completionStrategies": [s.value for s in CompletionStrategy],
        "coverageModes": [s.value for s in CoverageMode],
        "analysisIntents": [s.value for s in AnalysisIntent],
    }

    assert "INSIDER_ACTIVITY" in data["analysisIntents"]

