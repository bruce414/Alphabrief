"""Integration tests for POST /api/v1/quick-chat/analyze."""

from __future__ import annotations

import json

import pytest

from app.schemas.quick_chat import QuickChatAnalyzeErrorBody

VALID_ANALYSIS_JSON = json.dumps(
    {
        "analysis": {
            "summary": "U.S. tightened AI chip export rules.",
            "why_it_matters": "Limits China sales for leading GPU vendors.",
            "market_impact": "Nvidia and peers face revenue and supply-chain pressure.",
            "risks_and_uncertainties": "Policy scope and enforcement remain uncertain.",
            "watch_next": ["Nvidia earnings guidance", "Further U.S. rule updates"],
        },
        "market_map": {
            "nodes": [
                {
                    "id": "event_1",
                    "type": "main_event",
                    "label": "Export restrictions",
                    "description": "New U.S. AI chip export limits.",
                    "linked_section": "summary",
                    "confidence": "high",
                },
                {
                    "id": "company_nvda",
                    "type": "company",
                    "label": "Nvidia",
                    "description": "Direct exposure to AI accelerator sales.",
                    "linked_section": "market_impact",
                    "confidence": "high",
                },
                {
                    "id": "company_amd",
                    "type": "company",
                    "label": "AMD",
                    "description": "Competitor in data-center GPUs.",
                    "linked_section": "market_impact",
                    "confidence": "medium",
                },
                {
                    "id": "sector_semis",
                    "type": "sector_theme",
                    "label": "Semiconductors",
                    "description": "Sector sensitive to export policy.",
                    "linked_section": "market_impact",
                    "confidence": "high",
                },
                {
                    "id": "impact_china",
                    "type": "market_impact",
                    "label": "China revenue risk",
                    "description": "Potential lost sales in China.",
                    "linked_section": "risks_and_uncertainties",
                    "confidence": "medium",
                },
                {
                    "id": "risk_geo",
                    "type": "risk_uncertainty",
                    "label": "Geopolitical risk",
                    "description": "U.S.–China tech rivalry escalation.",
                    "linked_section": "risks_and_uncertainties",
                    "confidence": "high",
                },
                {
                    "id": "watch_earnings",
                    "type": "watch_next",
                    "label": "Earnings guidance",
                    "description": "Management commentary on China.",
                    "linked_section": "watch_next",
                    "confidence": "high",
                },
                {
                    "id": "watch_policy",
                    "type": "watch_next",
                    "label": "Policy updates",
                    "description": "Further rule clarifications.",
                    "linked_section": "watch_next",
                    "confidence": "medium",
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "event_1",
                    "target": "company_nvda",
                    "label": "affects",
                    "confidence": "high",
                },
                {
                    "id": "e2",
                    "source": "event_1",
                    "target": "company_amd",
                    "label": "may benefit",
                    "confidence": "medium",
                },
                {
                    "id": "e3",
                    "source": "company_nvda",
                    "target": "impact_china",
                    "label": "creates uncertainty around",
                    "confidence": "medium",
                },
                {
                    "id": "e4",
                    "source": "impact_china",
                    "target": "risk_geo",
                    "label": "linked to",
                    "confidence": "medium",
                },
                {
                    "id": "e5",
                    "source": "event_1",
                    "target": "sector_semis",
                    "label": "affects",
                    "confidence": "high",
                },
                {
                    "id": "e6",
                    "source": "sector_semis",
                    "target": "company_amd",
                    "label": "linked to",
                    "confidence": "medium",
                },
                {
                    "id": "e7",
                    "source": "risk_geo",
                    "target": "watch_policy",
                    "label": "watch next",
                    "confidence": "medium",
                },
                {
                    "id": "e8",
                    "source": "company_nvda",
                    "target": "watch_earnings",
                    "label": "watch next",
                    "confidence": "high",
                },
            ],
        },
    }
)

SOURCE_TEXT = (
    "The United States announced tighter export restrictions on advanced AI chips sold to China. "
    "Nvidia and other semiconductor companies may see reduced revenue from Chinese customers. "
    "Investors are watching earnings guidance and further policy updates for clarity on scope. "
) * 3


class _RecordingAnalysisClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = 0
        self.kwargs: list[dict] = []

    async def generate_quick_chat_analysis_json(self, **kwargs: object) -> str:
        self.kwargs.append(dict(kwargs))
        raw = self.responses[self.calls]
        self.calls += 1
        return raw


async def _register(client) -> None:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "quickchat@example.com", "password": "password123"},
    )
    assert reg.status_code == 201


@pytest.mark.asyncio
async def test_analyze_returns_parsed_json_with_mocked_client(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_client = _RecordingAnalysisClient([VALID_ANALYSIS_JSON])
    monkeypatch.setattr(
        "app.services.quick_chat_analysis_service.get_ai_provider_client",
        lambda: mock_client,
    )

    await _register(client)
    resp = await client.post(
        "/api/v1/quick-chat/analyze",
        json={"sourceText": SOURCE_TEXT, "userQuery": "How does this affect Nvidia?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"]["summary"].startswith("U.S. tightened")
    assert len(body["marketMap"]["nodes"]) == 8
    assert len(body["marketMap"]["edges"]) == 8
    assert mock_client.calls == 1


@pytest.mark.asyncio
async def test_analyze_retries_when_model_returns_invalid_json(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_client = _RecordingAnalysisClient(["not valid json", VALID_ANALYSIS_JSON])
    monkeypatch.setattr(
        "app.services.quick_chat_analysis_service.get_ai_provider_client",
        lambda: mock_client,
    )

    await _register(client)
    resp = await client.post(
        "/api/v1/quick-chat/analyze",
        json={"sourceText": SOURCE_TEXT},
    )
    assert resp.status_code == 200
    assert "analysis" in resp.json()
    assert mock_client.calls == 2
    second_call = mock_client.kwargs[1]
    assert second_call.get("prior_assistant_content") == "not valid json"
    assert second_call.get("follow_up_user_content")


@pytest.mark.asyncio
async def test_analyze_source_url_fetch_failure_returns_structured_error(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fail_fetch(
        url: str,
        *,
        http_client,
    ) -> tuple[None, QuickChatAnalyzeErrorBody]:
        _ = url, http_client
        return None, QuickChatAnalyzeErrorBody(
            error_code="SOURCE_FETCH_FAILED",
            message="Could not fetch source URL",
        )

    monkeypatch.setattr(
        "app.services.quick_chat_analysis_service.fetch_source_text_from_url",
        _fail_fetch,
    )

    await _register(client)
    resp = await client.post(
        "/api/v1/quick-chat/analyze",
        json={"sourceUrl": "https://example.com/article"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"]["errorCode"] == "SOURCE_FETCH_FAILED"
    assert "fetch" in body["error"]["message"].lower()
    assert "analysis" not in body
