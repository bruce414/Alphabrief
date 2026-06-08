from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import func, select

from app.models.source import Source
from app.models.source_fetch_log import SourceFetchLog
from app.models.source_fetch_policy import SourceFetchPolicy
from app.models.user import User
from app.services.scraping_policy import FetchDecision, evaluate_url, fetch_with_policy


@pytest.fixture(autouse=True)
def _reset_policy_state():
    import app.services.scraping_policy as sp

    sp._domain_buckets.clear()
    yield


async def _mk_user_and_source(db_session):
    u = User(email=f"u-{datetime.now(UTC).timestamp()}@example.com", password_hash="x")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)

    s = Source(
        user_id=u.id,
        source_type="ARTICLE_URL",
        source_access_method="SERVER_FETCH",
        source_access_status="PENDING",
        original_input="https://example.com/a",
        normalized_url=None,
        raw_text_retention="NOT_STORED",
        metadata_={},
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return u, s


@pytest.mark.asyncio
async def test_evaluate_url_invalid_scheme_blocked(db_session):
    res = await evaluate_url("ftp://example.com/a", db_session)
    assert res.decision == FetchDecision.BLOCKED
    assert res.reason == "invalid_scheme"


@pytest.mark.asyncio
async def test_evaluate_url_private_ip_blocked(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["192.168.1.10"])
    res = await evaluate_url("https://example.com/a", db_session)
    assert res.decision == FetchDecision.BLOCKED
    assert res.reason == "ssrf_private_ip"


@pytest.mark.asyncio
async def test_evaluate_url_rate_limited_after_burst(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    # Reset in-memory buckets for determinism.
    import app.services.scraping_policy as sp

    sp._domain_buckets.clear()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(500)

    url = "https://example.com/a"
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        r1 = await evaluate_url(url, db_session, http_client=client)
        r2 = await evaluate_url(url, db_session, http_client=client)
        r3 = await evaluate_url(url, db_session, http_client=client)
    assert r1.decision == FetchDecision.ALLOW
    assert r2.decision == FetchDecision.ALLOW
    assert r3.decision == FetchDecision.BLOCKED
    assert r3.reason == "rate_limited"


@pytest.mark.asyncio
async def test_rate_limit_is_per_domain(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    import app.services.scraping_policy as sp

    sp._domain_buckets.clear()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        a1 = await evaluate_url("https://a.example/a", db_session, http_client=client)
        a2 = await evaluate_url("https://a.example/b", db_session, http_client=client)
        b1 = await evaluate_url("https://b.example/a", db_session, http_client=client)
    assert a1.decision == FetchDecision.ALLOW
    assert a2.decision == FetchDecision.ALLOW
    assert b1.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_robots_fresh_cache_used(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    now = datetime.now(UTC)
    db_session.add(
        SourceFetchPolicy(
            domain="example.com",
            robots_txt_url="https://example.com/robots.txt",
            robots_txt_content="User-agent: *\nDisallow: /\n",
            robots_status=200,
            robots_fetched_at=now,
            robots_expires_at=now + timedelta(hours=24),
            metadata_={},
        )
    )
    await db_session.commit()

    # If a network fetch happens, fail the test.
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_disallow"


@pytest.mark.asyncio
async def test_robots_stale_cache_refetched(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    now = datetime.now(UTC)
    db_session.add(
        SourceFetchPolicy(
            domain="example.com",
            robots_txt_url="https://example.com/robots.txt",
            robots_txt_content="User-agent: *\nDisallow: /\n",
            robots_status=200,
            robots_fetched_at=now - timedelta(hours=48),
            robots_expires_at=now - timedelta(hours=1),
            metadata_={},
        )
    )
    await db_session.commit()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow:\n")
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_missing_robots_txt_means_allowed(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_malformed_robots_does_not_crash_and_means_allowed(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="not a robots file at all \x00\x00\x00")
        return httpx.Response(500)

    # Force robot parsing to throw to ensure the guard works.
    import app.services.scraping_policy as sp

    monkeypatch.setattr(sp.RobotFileParser, "parse", lambda _self, _lines: (_ for _ in ()).throw(Exception("boom")))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_robots_disallow_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_disallow"


@pytest.mark.asyncio
async def test_redirect_chain_landing_on_private_ip_is_blocked_and_logged(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda h: [h])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/start":
            return httpx.Response(302, headers={"Location": "http://192.168.1.3/private"})
        return httpx.Response(200, text="<html>ok</html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy(
            "http://198.51.100.1/start",
            db_session,
            u.id,
            s.id,
            http_client=client,
        )
    assert res.decision == FetchDecision.BLOCKED

    cnt = await db_session.scalar(
        select(func.count()).select_from(SourceFetchLog).where(SourceFetchLog.source_id == s.id)
    )
    assert cnt == 1


@pytest.mark.asyncio
async def test_401_403_response_becomes_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(403, text="<html>no</html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "auth_or_paywall"


@pytest.mark.asyncio
async def test_noai_header_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="<html><body>ok</body></html>",
            headers={"content-type": "text/html", "X-Robots-Tag": "noai"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "noai_header"


@pytest.mark.asyncio
async def test_noai_meta_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = '<html><head><meta name="robots" content="noai"></head><body>x</body></html>'

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "noai_meta"


@pytest.mark.asyncio
async def test_paywall_marker_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = "<html><body>Subscribe to continue</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "paywall_detected"


@pytest.mark.asyncio
async def test_paywall_classname_in_bundle_does_not_trigger_paywall_detected(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    # Simulate a public article page that includes a JS bundle mentioning ".paywall"
    # but does not display paywall messaging to the user.
    html = """
    <html>
      <head>
        <script>
          // bundle content
          const css = '.paywall{display:none} .subscription-wall{opacity:0}';
        </script>
      </head>
      <body>
        <article><p>This is a public article with readable content.</p></article>
      </body>
    </html>
    """
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)

    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_paywall_keyword_in_footer_outside_article_does_not_trigger(db_session, monkeypatch):
    """A free article on a site that runs a paywall tier should not be flagged
    just because the page chrome (footer/CTA) contains paywall copy."""
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = """
    <html>
      <body>
        <article><p>This is a free finance article with full content.</p></article>
        <footer><a href="/plans">Subscribe to continue with our newsletter</a></footer>
      </body>
    </html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_iaff_meta_false_returns_paywall_detected(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = (
        '<html><head>'
        '<meta itemprop="isAccessibleForFree" content="False">'
        '</head><body><article>teaser</article></body></html>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "paywall_detected"


@pytest.mark.asyncio
async def test_iaff_jsonld_false_returns_paywall_detected(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = """
    <html><head>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"NewsArticle","isAccessibleForFree":false}
    </script>
    </head><body><article>teaser</article></body></html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "paywall_detected"


@pytest.mark.asyncio
async def test_iaff_true_overrides_keyword_marker(db_session, monkeypatch):
    """Explicit free signal must beat substring matches that would otherwise
    trip a paywall heuristic — the publisher tells us this article is free."""
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = (
        '<html><head>'
        '<meta itemprop="isAccessibleForFree" content="True">'
        '</head><body>Subscribe to continue is the name of our newsletter.</body></html>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_robots_5xx_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(503, text="oh no")
        return httpx.Response(200, text="<html>x</html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_unavailable"


@pytest.mark.asyncio
async def test_robots_403_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(403, text="forbidden")
        return httpx.Response(200, text="<html>x</html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_forbidden"


@pytest.mark.asyncio
async def test_robots_network_error_returns_metadata_only(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            raise httpx.ReadTimeout("simulated timeout", request=request)
        return httpx.Response(200, text="<html>x</html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await evaluate_url("https://example.com/a", db_session, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_unavailable"


@pytest.mark.asyncio
async def test_cross_origin_redirect_re_evaluates_robots(db_session, monkeypatch):
    """Aggregator → publisher hops must run under the publisher's robots.txt,
    not the aggregator's. If the publisher disallows, the fetch becomes
    METADATA_ONLY even though the aggregator allowed crawling."""
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        path = request.url.path
        if path == "/robots.txt" and host == "aggregator.example":
            return httpx.Response(404)
        if path == "/robots.txt" and host == "publisher.example":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        if host == "aggregator.example" and path == "/news/x":
            return httpx.Response(302, headers={"Location": "https://publisher.example/article/y"})
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy(
            "https://aggregator.example/news/x", db_session, u.id, s.id, http_client=client
        )
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "robots_disallow"
    assert res.final_url == "https://publisher.example/article/y"


@pytest.mark.asyncio
async def test_cross_origin_redirect_to_denylisted_domain_blocked(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.host == "aggregator.example":
            return httpx.Response(302, headers={"Location": "https://internal.mil/leak"})
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy(
            "https://aggregator.example/x", db_session, u.id, s.id, http_client=client
        )
    assert res.decision == FetchDecision.BLOCKED
    assert res.reason == "domain_denied"


@pytest.mark.asyncio
async def test_same_host_redirect_does_not_double_evaluate(db_session, monkeypatch):
    """Same-host redirects (http→https, www→non-www, trailing slash) should not
    consume an extra rate-limit token for the same host."""
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/old":
            return httpx.Response(301, headers={"Location": "/new"})
        return httpx.Response(200, text="<html><body>ok</body></html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        # Burst is 2; with a same-host redirect chain consuming only one token,
        # we should still have headroom for a second fetch.
        r1 = await fetch_with_policy("https://example.com/old", db_session, u.id, s.id, http_client=client)
        r2 = await fetch_with_policy("https://example.com/other", db_session, u.id, s.id, http_client=client)
    assert r1.decision == FetchDecision.ALLOW
    assert r2.decision == FetchDecision.ALLOW


@pytest.mark.asyncio
async def test_canonical_url_extracted_from_link_tag(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = (
        '<html><head>'
        '<link rel="canonical" href="https://publisher.example/article/123">'
        '</head><body><article>content</article></body></html>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://aggregator.example/x", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.ALLOW
    assert res.canonical_url == "https://publisher.example/article/123"


@pytest.mark.asyncio
async def test_canonical_url_falls_back_to_og_url(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = (
        '<html><head>'
        '<meta property="og:url" content="https://publisher.example/article/abc">'
        '</head><body><article>content</article></body></html>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/x", db_session, u.id, s.id, http_client=client)
    assert res.canonical_url == "https://publisher.example/article/abc"


@pytest.mark.asyncio
async def test_canonical_url_relative_resolved_against_final_url(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = '<html><head><link rel="canonical" href="/canonical/path"></head><body>x</body></html>'

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/article", db_session, u.id, s.id, http_client=client)
    assert res.canonical_url == "https://example.com/canonical/path"


@pytest.mark.asyncio
async def test_canonical_url_extracted_even_on_paywall(db_session, monkeypatch):
    """Even when we fall back to METADATA_ONLY due to paywall, the canonical is
    still the right citation target — keep extracting it."""
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    html = (
        '<html><head>'
        '<meta itemprop="isAccessibleForFree" content="False">'
        '<link rel="canonical" href="https://publisher.example/locked/article">'
        '</head><body><article>teaser</article></body></html>'
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text=html, headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        res = await fetch_with_policy("https://example.com/x", db_session, u.id, s.id, http_client=client)
    assert res.decision == FetchDecision.METADATA_ONLY
    assert res.reason == "paywall_detected"
    assert res.canonical_url == "https://publisher.example/locked/article"


@pytest.mark.asyncio
async def test_every_fetch_attempt_writes_exactly_one_log_row(db_session, monkeypatch):
    monkeypatch.setattr("app.services.scraping_policy.resolve_host_ips", lambda _h: ["93.184.216.34"])
    u, s = await _mk_user_and_source(db_session)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, text="<html><body>ok</body></html>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await fetch_with_policy("https://example.com/a", db_session, u.id, s.id, http_client=client)

    cnt = await db_session.scalar(
        select(func.count()).select_from(SourceFetchLog).where(SourceFetchLog.source_id == s.id)
    )
    assert cnt == 1

