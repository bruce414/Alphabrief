"""Source ingestion integration tests (network calls mocked)."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import func, select

from app.api.deps import get_http_client
from app.services.scraping_policy import FetchDecision, FetchResult
from app.main import app
from app.models.source_fetch_log import SourceFetchLog
from app.models.usage_event import UsageEvent


FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"


async def _register(client, email: str, password: str = "password123") -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_post_sources_requires_authentication(client):
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/a"},
    )
    assert r.status_code == 401
    assert r.json()["errorCode"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_other_users_source_returns_forbidden(client, monkeypatch):
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    await _register(client, "alice-sources@example.com")
    created = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/a"},
    )
    assert created.status_code == 201
    sid = created.json()["sourceId"]

    await client.post("/api/v1/auth/logout")
    await _register(client, "bob-sources@example.com")

    r = await client.get(f"/api/v1/sources/{sid}")
    assert r.status_code == 403
    assert r.json()["errorCode"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_invalid_scheme_returns_invalid_url(client):
    await _register(client, "invalid-scheme@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "ftp://example.com/a"},
    )
    assert r.status_code == 400
    assert r.json()["errorCode"] == "INVALID_URL"


@pytest.mark.asyncio
async def test_localhost_blocked(client):
    await _register(client, "localhost@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "http://localhost/path"},
    )
    assert r.status_code == 403
    assert r.json()["errorCode"] == "SOURCE_BLOCKED"


@pytest.mark.asyncio
async def test_private_ip_literal_blocked(client):
    await _register(client, "private-ip@example.com")
    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "http://192.168.1.1/x"},
    )
    assert r.status_code == 403
    assert r.json()["errorCode"] == "SOURCE_BLOCKED"


@pytest.mark.asyncio
async def test_redirect_to_private_ip_blocked(client):
    await _register(client, "redirect@example.com")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "198.51.100.1":
            return httpx.Response(
                302,
                headers={"Location": "http://192.168.1.3/private"},
            )
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)

    async def override_http():
        async with httpx.AsyncClient(transport=transport, timeout=30.0) as c:
            yield c

    app.dependency_overrides[get_http_client] = override_http
    try:
        r = await client.post(
            "/api/v1/sources",
            json={
                "sourceType": "ARTICLE_URL",
                "input": "http://198.51.100.1/start",
            },
        )
        assert r.status_code == 403
        assert r.json()["errorCode"] == "SOURCE_BLOCKED"
    finally:
        app.dependency_overrides.pop(get_http_client, None)


@pytest.mark.asyncio
async def test_article_canonical_url_persisted_and_surfaced(client, monkeypatch):
    """When the fetched page declares a canonical URL pointing to the original
    publisher, the source row stores it and the API response surfaces it."""
    await _register(client, "canonical@example.com")
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="aggregator.example",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
            content_type="text/html",
            canonical_url="https://publisher.example/original/article",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    created = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://aggregator.example/syndicated"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["canonicalUrl"] == "https://publisher.example/original/article"

    sid = created.json()["sourceId"]
    detail = await client.get(f"/api/v1/sources/{sid}")
    assert detail.status_code == 200
    assert detail.json()["canonicalUrl"] == "https://publisher.example/original/article"


@pytest.mark.asyncio
async def test_article_no_canonical_url_returns_null(client, monkeypatch):
    await _register(client, "no-canonical@example.com")
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/a"},
    )
    assert r.status_code == 201
    assert r.json()["canonicalUrl"] is None


@pytest.mark.asyncio
async def test_article_happy_path_full_text_extracted(client, monkeypatch):
    await _register(client, "happy@example.com")
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    r = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "ARTICLE_URL",
            "input": "https://example.com/market-news",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["sourceAccessStatus"] == "FULL_TEXT_EXTRACTED"
    assert body["sourceAccessMethod"] == "SERVER_FETCH"
    assert body["extractedTextWordCount"] is not None and body["extractedTextWordCount"] >= 200


@pytest.mark.asyncio
async def test_article_http_403_returns_metadata_only(client, monkeypatch):
    await _register(client, "meta403@example.com")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=403,
            headers={"content-type": "text/html"},
            content=b"<html><title>T</title><body><p>x</p></body></html>",
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/wall"},
    )
    assert r.status_code == 201
    assert r.json()["sourceAccessStatus"] == "METADATA_ONLY"


@pytest.mark.asyncio
async def test_article_low_word_count_metadata_or_low_confidence(client, monkeypatch):
    await _register(client, "lowtext@example.com")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        html = "<html><body><article><p>Too short.</p></article></body></html>"
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html"},
            content=html.encode(),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/short"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["sourceAccessStatus"] in ("METADATA_ONLY", "FULL_TEXT_EXTRACTED")
    if body["sourceAccessStatus"] == "FULL_TEXT_EXTRACTED":
        assert body["extractionConfidence"] == "LOW"


@pytest.mark.asyncio
async def test_youtube_transcript_full_text(client, monkeypatch):
    await _register(client, "yt-tx@example.com")

    async def fake_oembed(url: str, **kwargs):  # noqa: ANN003
        return {
            "title": "Video Title",
            "author_name": "Channel Name",
        }

    monkeypatch.setattr("app.services.source_extraction_service.fetch_oembed", fake_oembed)
    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_transcript_text",
        AsyncMock(return_value=" ".join(["word"] * 300)),
    )

    r = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "YOUTUBE_URL",
            "input": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["sourceAccessMethod"] == "YOUTUBE_TRANSCRIPT"
    assert body["sourceAccessStatus"] == "FULL_TEXT_EXTRACTED"

    source_id = body["sourceId"]
    detail = await client.get(f"/api/v1/sources/{source_id}")
    assert detail.status_code == 200
    assert detail.json()["extractedText"] is not None


@pytest.mark.asyncio
async def test_youtube_no_transcript_metadata_only(client, monkeypatch):
    await _register(client, "yt-meta@example.com")

    async def fake_oembed(url: str, **kwargs):  # noqa: ANN003
        return {"title": "T", "author_name": "C"}

    monkeypatch.setattr("app.services.source_extraction_service.fetch_oembed", fake_oembed)
    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_transcript_text",
        AsyncMock(return_value=None),
    )

    r = await client.post(
        "/api/v1/sources",
        json={
            "sourceType": "YOUTUBE_URL",
            "input": "https://youtu.be/dQw4w9WgXcQ",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["sourceAccessMethod"] == "YOUTUBE_METADATA"
    assert body["sourceAccessStatus"] == "METADATA_ONLY"


@pytest.mark.asyncio
async def test_usage_event_recorded_for_source_extraction(client, db_session, monkeypatch):
    await _register(client, "usage@example.com")
    html = (FIXTURES / "long_article.html").read_text(encoding="utf-8")

    async def fake_fetch_with_policy(start_url: str, **kwargs):  # noqa: ANN003
        return FetchResult(
            final_url=start_url,
            domain="example.com",
            decision=FetchDecision.ALLOW,
            reason="ok",
            status_code=200,
            headers={"content-type": "text/html"},
            content=html.encode("utf-8"),
            content_type="text/html",
        )

    monkeypatch.setattr(
        "app.services.source_extraction_service.fetch_with_policy",
        fake_fetch_with_policy,
    )

    before = await db_session.scalar(
        select(func.count()).select_from(UsageEvent).where(UsageEvent.event_type == "SOURCE_EXTRACTION")
    )

    r = await client.post(
        "/api/v1/sources",
        json={"sourceType": "ARTICLE_URL", "input": "https://example.com/u"},
    )
    assert r.status_code == 201

    after = await db_session.scalar(
        select(func.count()).select_from(UsageEvent).where(UsageEvent.event_type == "SOURCE_EXTRACTION")
    )
    assert after == before + 1


@pytest.mark.asyncio
async def test_source_fetch_log_written_for_each_attempt(client, db_session, monkeypatch):
    await _register(client, "fetchlog@example.com")

    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="<html><body>" + "word " * 250 + "</body></html>",
            headers={"content-type": "text/html"},
        )

    transport = httpx.MockTransport(handler)

    async def override_http():
        async with httpx.AsyncClient(transport=transport, timeout=30.0) as c:
            yield c

    app.dependency_overrides[get_http_client] = override_http
    try:
        r = await client.post(
            "/api/v1/sources",
            json={"sourceType": "ARTICLE_URL", "input": "https://example.com/a"},
        )
        assert r.status_code == 201, r.text
        sid = r.json()["sourceId"]

        cnt = await db_session.scalar(
            select(func.count())
            .select_from(SourceFetchLog)
            .where(SourceFetchLog.source_id == UUID(sid))
        )
        assert cnt == 1
    finally:
        app.dependency_overrides.pop(get_http_client, None)


@pytest.mark.asyncio
async def test_robots_disallowed_article_is_metadata_only_and_does_not_fetch_body(client, monkeypatch):
    await _register(client, "robotsdisallow@example.com")

    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    non_robots_calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        non_robots_calls["count"] += 1
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)

    async def override_http():
        async with httpx.AsyncClient(transport=transport, timeout=30.0) as c:
            yield c

    app.dependency_overrides[get_http_client] = override_http
    try:
        r = await client.post(
            "/api/v1/sources",
            json={"sourceType": "ARTICLE_URL", "input": "https://example.com/a"},
        )
        assert r.status_code == 201, r.text
        assert r.json()["sourceAccessStatus"] == "METADATA_ONLY"
        assert non_robots_calls["count"] == 0
    finally:
        app.dependency_overrides.pop(get_http_client, None)
