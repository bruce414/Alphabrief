from __future__ import annotations

import asyncio
import ipaddress
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.source_fetch_log import SourceFetchLog
from app.repositories.source_fetch_log_repository import SourceFetchLogRepository
from app.repositories.source_fetch_policy_repository import SourceFetchPolicyRepository
from app.services.url_safety_service import resolve_host_ips


class FetchDecision(str, Enum):
    ALLOW = "ALLOW"
    METADATA_ONLY = "METADATA_ONLY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class FetchPolicyResult:
    decision: FetchDecision
    reason: str
    domain: str


@dataclass(frozen=True)
class FetchResult:
    final_url: str
    domain: str
    decision: FetchDecision
    reason: str
    status_code: int | None
    headers: dict[str, str]
    content: bytes | None
    content_type: str | None
    canonical_url: str | None = None


_rate_lock = asyncio.Lock()
_domain_buckets: dict[str, dict[str, float]] = {}


def _is_private_or_blocked_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _get_domain(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    return host


def _matches_suffix_denylist(domain: str, suffixes: list[str]) -> bool:
    d = domain.lower().rstrip(".")
    for suf in suffixes:
        s = suf.strip().lower()
        if not s:
            continue
        s = s.lstrip(".")
        if not s:
            continue
        if d == s or d.endswith(f".{s}"):
            return True
    return False


async def _rate_limit_allow(domain: str) -> bool:
    """
    Token bucket:
    - refill: 6 tokens/minute
    - capacity (burst): 2
    - cost: 1 token per request
    """
    settings = get_settings()
    refill_per_min = 6.0
    capacity = 2.0

    # Allow future tuning via settings without breaking defaults.
    refill_per_min = float(getattr(settings, "source_fetch_rate_limit_per_minute", refill_per_min))
    capacity = float(getattr(settings, "source_fetch_rate_limit_burst", capacity))

    rate_per_sec = refill_per_min / 60.0
    now = time.monotonic()

    async with _rate_lock:
        b = _domain_buckets.get(domain)
        if b is None:
            b = {"tokens": capacity, "ts": now}
            _domain_buckets[domain] = b
        else:
            elapsed = max(0.0, now - b["ts"])
            b["tokens"] = min(capacity, b["tokens"] + elapsed * rate_per_sec)
            b["ts"] = now

        if b["tokens"] < 1.0:
            return False
        b["tokens"] -= 1.0
        return True


async def _validate_scheme_and_dns(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "invalid_scheme"
    domain = _get_domain(url)
    if not domain:
        return False, "invalid_host"

    # Resolve A/AAAA and block if ANY IP is private/loopback/link-local/ULA.
    def _resolve() -> tuple[bool, str]:
        ips = resolve_host_ips(domain)
        if not ips:
            return False, "dns_no_records"
        for ip in ips:
            if _is_private_or_blocked_ip(ip):
                return False, "ssrf_private_ip"
        return True, "ok"

    return await asyncio.to_thread(_resolve)


async def evaluate_url(
    url: str,
    db: AsyncSession,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> FetchPolicyResult:
    settings = get_settings()
    domain = _get_domain(url)

    ok, reason = await _validate_scheme_and_dns(url)
    if not ok:
        return FetchPolicyResult(decision=FetchDecision.BLOCKED, reason=reason, domain=domain or "")

    # Denylist: always include .mil, plus configured suffixes.
    deny_suffixes = list(settings.source_domain_denylist_suffixes())
    if ".mil" not in [s.lower().strip() for s in deny_suffixes]:
        deny_suffixes.append(".mil")
    if _matches_suffix_denylist(domain, deny_suffixes):
        return FetchPolicyResult(decision=FetchDecision.BLOCKED, reason="domain_denied", domain=domain)

    # Per-domain rate limit.
    if not await _rate_limit_allow(domain):
        return FetchPolicyResult(decision=FetchDecision.BLOCKED, reason="rate_limited", domain=domain)

    # robots.txt: cached in DB; refetch if missing/stale (> 24h or past expires_at).
    ttl_hours = int(getattr(settings, "robots_cache_ttl_hours", 24))
    now = datetime.now(UTC)

    policy_repo = SourceFetchPolicyRepository(db)
    cached = await policy_repo.get_by_domain(domain)
    cached_fresh = False
    if cached and cached.robots_fetched_at:
        if cached.robots_expires_at and cached.robots_expires_at > now:
            cached_fresh = True
        elif cached.robots_fetched_at > now - timedelta(hours=ttl_hours):
            cached_fresh = True

    if not cached_fresh:
        robots_url = f"https://{domain}/robots.txt"
        robots_timeout = float(getattr(settings, "robots_timeout_seconds", 5.0))
        robots_max_bytes = int(getattr(settings, "robots_max_bytes", 100 * 1024))
        robots_failure_ttl_hours = int(getattr(settings, "robots_failure_ttl_hours", 1))

        robots_status: int | None = None
        robots_body: str | None = None
        robots_meta: dict[str, Any] = {}
        fetched_at = now

        own_client = http_client is None
        client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                timeout=robots_timeout,
                connect=robots_timeout,
                read=robots_timeout,
                write=robots_timeout,
                pool=robots_timeout,
            ),
            follow_redirects=True,
            headers={"User-Agent": settings.http_user_agent, "Accept": "text/plain,*/*"},
        )
        try:
            try:
                async with client.stream("GET", robots_url) as resp:
                    robots_status = resp.status_code
                    buf = bytearray()
                    async for chunk in resp.aiter_bytes():
                        buf.extend(chunk)
                        if len(buf) > robots_max_bytes:
                            robots_meta["truncated"] = True
                            break
                    if resp.status_code == 404:
                        robots_body = None
                    else:
                        robots_body = buf.decode("utf-8", errors="replace").replace("\x00", "")
            except httpx.TimeoutException:
                robots_meta["fetchError"] = "timeout"
            except httpx.HTTPError as exc:
                robots_meta["fetchError"] = exc.__class__.__name__
        finally:
            if own_client:
                await client.aclose()

        # Per RFC 9309, robots fetch failures (5xx, 401/403, network errors) imply a
        # *temporary* disallow. Cache them briefly so we re-probe sooner than the
        # 24h success TTL.
        is_failure = (
            robots_meta.get("fetchError") is not None
            or robots_status in (401, 403)
            or (robots_status is not None and 500 <= robots_status < 600)
        )
        expires_at = now + timedelta(hours=robots_failure_ttl_hours if is_failure else ttl_hours)

        await policy_repo.upsert_robots(
            domain=domain,
            robots_txt_url=robots_url,
            robots_txt_content=robots_body,
            robots_status=robots_status,
            fetched_at=fetched_at,
            expires_at=expires_at,
            metadata=robots_meta,
        )

        cached = await policy_repo.get_by_domain(domain)

    # Apply RFC 9309 outcomes from cache.
    robots_txt = cached.robots_txt_content if cached else None
    robots_status = cached.robots_status if cached else None
    cached_meta = (cached.metadata_ if cached else None) or {}
    fetch_error = cached_meta.get("fetchError")

    # 5xx or network error: server reachable-but-broken, treat as temporary disallow.
    if fetch_error or (robots_status is not None and 500 <= robots_status < 600):
        return FetchPolicyResult(
            decision=FetchDecision.METADATA_ONLY,
            reason="robots_unavailable",
            domain=domain,
        )
    # 401/403 on robots.txt: server is actively gating crawlers, honor that.
    if robots_status in (401, 403):
        return FetchPolicyResult(
            decision=FetchDecision.METADATA_ONLY,
            reason="robots_forbidden",
            domain=domain,
        )
    # 404 (or 2xx with empty body): no rules apply.
    if robots_status == 404 or not robots_txt:
        return FetchPolicyResult(decision=FetchDecision.ALLOW, reason="ok", domain=domain)

    # Parse robots. Malformed means allow (but keep metadata for audit).
    rp = RobotFileParser()
    try:
        rp.parse(robots_txt.splitlines())
        allow_for_ua = rp.can_fetch("AlphaBriefBot/0.1", url) and rp.can_fetch("*", url)
    except Exception:
        allow_for_ua = True

    if not allow_for_ua:
        return FetchPolicyResult(
            decision=FetchDecision.METADATA_ONLY,
            reason="robots_disallow",
            domain=domain,
        )

    return FetchPolicyResult(decision=FetchDecision.ALLOW, reason="ok", domain=domain)


async def _validate_redirect_target(url: str) -> tuple[bool, str]:
    ok, reason = await _validate_scheme_and_dns(url)
    if not ok:
        return False, reason

    settings = get_settings()
    domain = _get_domain(url)
    deny_suffixes = list(settings.source_domain_denylist_suffixes())
    if ".mil" not in [s.lower().strip() for s in deny_suffixes]:
        deny_suffixes.append(".mil")
    if _matches_suffix_denylist(domain, deny_suffixes):
        return False, "domain_denied"
    return True, "ok"


def _header_contains_token(header_val: str | None, token: str) -> bool:
    if not header_val:
        return False
    return token.lower() in header_val.lower()


def _html_contains_noai_meta(html: str) -> bool:
    s = html.lower()
    return ("<meta" in s) and ("noai" in s) and ("robots" in s)


_ARTICLE_TAG_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.DOTALL | re.IGNORECASE)
_ARTICLE_BODY_ITEMPROP_RE = re.compile(
    r'<(\w+)[^>]+itemprop\s*=\s*["\']?articleBody["\']?[^>]*>(.*?)</\1>',
    re.DOTALL | re.IGNORECASE,
)
_MAIN_TAG_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.DOTALL | re.IGNORECASE)

_META_TAG_RE = re.compile(r"<meta\b([^>]*)>", re.IGNORECASE)
_META_IAFF_NAME_RE = re.compile(
    r'(?:itemprop|name)\s*=\s*["\']?isAccessibleForFree["\']?',
    re.IGNORECASE,
)
_META_CONTENT_RE = re.compile(r'content\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_JSONLD_BLOCK_RE = re.compile(
    r'<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

# Phrases tightly associated with paywall prompts. Kept narrow because the match
# runs against article-scoped HTML and we still want to avoid false positives on
# free pages that link to premium content.
_PAYWALL_MARKERS = (
    "subscribe to continue",
    "subscribe to read",
    "register to read",
    "register to continue",
    "sign in to continue reading",
    "sign in to read this",
    "this article is for subscribers",
    "this story is for subscribers",
    "subscribers only",
    "create a free account to continue",
    "unlock this article",
    "unlock with subscription",
)


def _extract_article_body(html: str) -> str:
    """Return the inner HTML of the article container, or the full HTML as fallback."""
    m = _ARTICLE_TAG_RE.search(html)
    if m:
        return m.group(1)
    m = _ARTICLE_BODY_ITEMPROP_RE.search(html)
    if m:
        return m.group(2)
    m = _MAIN_TAG_RE.search(html)
    if m:
        return m.group(1)
    return html


def _coerce_iaff_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("false", "no", "0"):
            return False
        if s in ("true", "yes", "1"):
            return True
    return None


def _collect_iaff_signals(node: Any, out: list[bool]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "isAccessibleForFree":
                coerced = _coerce_iaff_value(v)
                if coerced is not None:
                    out.append(coerced)
            else:
                _collect_iaff_signals(v, out)
    elif isinstance(node, list):
        for item in node:
            _collect_iaff_signals(item, out)


def _extract_is_accessible_for_free(html: str) -> bool | None:
    """Read schema.org `isAccessibleForFree` from <meta> and JSON-LD.

    Returns False if any block marks the page as paywalled, True if any marks it
    free (and none mark it paywalled), None when no signal is present. The
    "any-False wins" rule mirrors how publishers gate per-article content.
    """
    signals: list[bool] = []

    for m in _META_TAG_RE.finditer(html):
        attrs = m.group(1)
        if not _META_IAFF_NAME_RE.search(attrs):
            continue
        cm = _META_CONTENT_RE.search(attrs)
        if not cm:
            continue
        coerced = _coerce_iaff_value(cm.group(1))
        if coerced is not None:
            signals.append(coerced)

    for m in _JSONLD_BLOCK_RE.finditer(html):
        raw = m.group(1).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue
        _collect_iaff_signals(data, signals)

    if any(s is False for s in signals):
        return False
    if any(s is True for s in signals):
        return True
    return None


def _html_contains_paywall_marker(html: str) -> bool:
    body = _extract_article_body(html).lower()
    return any(m in body for m in _PAYWALL_MARKERS)


_LINK_TAG_RE = re.compile(r"<link\b([^>]*)>", re.IGNORECASE)
_LINK_REL_CANONICAL_RE = re.compile(r'rel\s*=\s*["\']?canonical["\']?', re.IGNORECASE)
_LINK_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_META_PROPERTY_OG_URL_RE = re.compile(
    r'(?:property|name)\s*=\s*["\']og:url["\']', re.IGNORECASE
)


def _extract_canonical_url(html: str, base_url: str) -> str | None:
    """Read the publisher-declared canonical URL.

    Prefers `<link rel="canonical">`, falls back to `<meta property="og:url">`.
    Resolves relative URLs against the final fetch URL.
    """
    for m in _LINK_TAG_RE.finditer(html):
        attrs = m.group(1)
        if not _LINK_REL_CANONICAL_RE.search(attrs):
            continue
        href_m = _LINK_HREF_RE.search(attrs)
        if href_m:
            href = href_m.group(1).strip()
            if href:
                return urljoin(base_url, href)

    for m in _META_TAG_RE.finditer(html):
        attrs = m.group(1)
        if not _META_PROPERTY_OG_URL_RE.search(attrs):
            continue
        cm = _META_CONTENT_RE.search(attrs)
        if cm:
            val = cm.group(1).strip()
            if val:
                return urljoin(base_url, val)

    return None


async def fetch_with_policy(
    url: str,
    db: AsyncSession,
    user_id,
    source_id,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> FetchResult:
    settings = get_settings()
    eval_result = await evaluate_url(url, db, http_client=http_client)
    domain = eval_result.domain

    log_repo = SourceFetchLogRepository(db)

    async def _write_log(
        *,
        final_url: str,
        decision: FetchDecision,
        reason: str,
        robots_decision: str | None,
        response_status: int | None,
        content_length: int | None,
        action_taken: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await log_repo.create(
            SourceFetchLog(
                user_id=user_id,
                source_id=source_id,
                domain=domain or _get_domain(final_url),
                url=final_url,
                robots_decision=robots_decision,
                response_status=response_status,
                content_length=content_length,
                action_taken=action_taken,
                denied_reason=reason if decision != FetchDecision.ALLOW else None,
                metadata_=metadata or {},
            )
        )

    if eval_result.decision == FetchDecision.BLOCKED:
        await _write_log(
            final_url=url,
            decision=FetchDecision.BLOCKED,
            reason=eval_result.reason,
            robots_decision=None,
            response_status=None,
            content_length=None,
            action_taken="BLOCKED",
            metadata={"stage": "pre_fetch"},
        )
        return FetchResult(
            final_url=url,
            domain=domain,
            decision=FetchDecision.BLOCKED,
            reason=eval_result.reason,
            status_code=None,
            headers={},
            content=None,
            content_type=None,
        )

    if eval_result.decision == FetchDecision.METADATA_ONLY:
        await _write_log(
            final_url=url,
            decision=FetchDecision.METADATA_ONLY,
            reason=eval_result.reason,
            robots_decision=eval_result.reason,
            response_status=None,
            content_length=None,
            action_taken="METADATA_ONLY",
            metadata={"stage": "pre_fetch"},
        )
        return FetchResult(
            final_url=url,
            domain=domain,
            decision=FetchDecision.METADATA_ONLY,
            reason=eval_result.reason,
            status_code=None,
            headers={},
            content=None,
            content_type=None,
        )

    # Allowed: fetch body with manual redirect validation and max bytes.
    timeout = httpx.Timeout(timeout=30.0, connect=10.0, read=30.0, write=30.0, pool=30.0)
    headers = {
        "User-Agent": getattr(settings, "scraping_user_agent", "AlphaBriefBot/0.1 (+https://alphabrief.com/bot)"),
        "Accept": "text/html,application/xhtml+xml,*/*",
    }
    max_bytes = int(getattr(settings, "max_fetch_bytes", 5 * 1024 * 1024))

    own_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    final_url = url
    status_code: int | None = None
    resp_headers: dict[str, str] = {}
    content: bytes | None = None
    content_type: str | None = None
    decision = FetchDecision.ALLOW
    reason = "ok"
    robots_decision = None
    metadata: dict[str, Any] = {}

    try:
        current = url
        current_host = _get_domain(current)
        for _ in range(15):
            ok, r_reason = await _validate_redirect_target(current)
            if not ok:
                decision = FetchDecision.BLOCKED
                reason = r_reason
                final_url = current
                break

            async with client.stream("GET", current, headers=headers, follow_redirects=False) as resp:
                status_code = resp.status_code
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                if resp.status_code in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("location")
                    if not loc:
                        decision = FetchDecision.METADATA_ONLY
                        reason = "redirect_missing_location"
                        final_url = str(resp.url)
                        break
                    current = urljoin(str(resp.url), loc)
                    new_host = _get_domain(current)

                    # Cross-origin hop: re-evaluate the new origin's robots.txt,
                    # denylist, and per-host rate limit. Aggregator → publisher
                    # redirects must not run under the aggregator's policy.
                    if new_host and new_host != current_host:
                        eval_redirect = await evaluate_url(current, db, http_client=client)
                        if eval_redirect.decision != FetchDecision.ALLOW:
                            decision = eval_redirect.decision
                            reason = eval_redirect.reason
                            final_url = current
                            metadata["redirectCrossOriginTo"] = current
                            metadata["redirectCrossOriginFromHost"] = current_host
                            break
                        current_host = new_host
                    continue

                buf = bytearray()
                async for chunk in resp.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > max_bytes:
                        decision = FetchDecision.METADATA_ONLY
                        reason = "body_too_large"
                        metadata["bodyTruncatedAtBytes"] = len(buf)
                        break
                final_url = str(resp.url)
                content = bytes(buf)
                ctype_raw = resp.headers.get("content-type")
                content_type = ctype_raw.split(";")[0].strip().lower() if ctype_raw else None
                break
        else:
            decision = FetchDecision.METADATA_ONLY
            reason = "too_many_redirects"

        # Post-fetch gates (only when we actually got a response body/status).
        if decision == FetchDecision.ALLOW and status_code is not None:
            if status_code in (401, 402, 403):
                decision = FetchDecision.METADATA_ONLY
                reason = "auth_or_paywall"
            elif status_code >= 400:
                decision = FetchDecision.METADATA_ONLY
                reason = "fetch_failed"
            elif content_type and ("html" not in content_type and "xhtml" not in content_type):
                decision = FetchDecision.METADATA_ONLY
                reason = "unsupported_content_type"

            if decision == FetchDecision.ALLOW:
                if _header_contains_token(resp_headers.get("x-robots-tag"), "noai"):
                    decision = FetchDecision.METADATA_ONLY
                    reason = "noai_header"

            if decision == FetchDecision.ALLOW and content:
                html_str = content.decode("utf-8", errors="replace")
                if _html_contains_noai_meta(html_str):
                    decision = FetchDecision.METADATA_ONLY
                    reason = "noai_meta"
                else:
                    # Authoritative publisher signal beats keyword heuristics:
                    # explicit `isAccessibleForFree=False` → paywall;
                    # explicit True → trust it and skip the keyword scan.
                    iaff = _extract_is_accessible_for_free(html_str)
                    if iaff is False:
                        decision = FetchDecision.METADATA_ONLY
                        reason = "paywall_detected"
                    elif iaff is None and _html_contains_paywall_marker(html_str):
                        decision = FetchDecision.METADATA_ONLY
                        reason = "paywall_detected"

        # Canonical URL: publisher's own declaration of where this content lives.
        # Extract whenever we have a body, regardless of final decision — even on
        # a paywalled fetch the canonical is the right citation target.
        canonical_url: str | None = None
        if content:
            try:
                canonical_url = _extract_canonical_url(
                    content.decode("utf-8", errors="replace"), final_url
                )
            except Exception:
                canonical_url = None
        if canonical_url:
            metadata["canonicalUrl"] = canonical_url

        action_taken = "FETCHED_BODY" if (content is not None and status_code is not None) else "NO_FETCH"
        if decision != FetchDecision.ALLOW:
            action_taken = "METADATA_ONLY" if decision == FetchDecision.METADATA_ONLY else "BLOCKED"

        await _write_log(
            final_url=final_url,
            decision=decision,
            reason=reason,
            robots_decision=robots_decision,
            response_status=status_code,
            content_length=len(content) if content is not None else None,
            action_taken=action_taken,
            metadata=metadata,
        )

        return FetchResult(
            final_url=final_url,
            domain=_get_domain(final_url),
            decision=decision,
            reason=reason,
            status_code=status_code,
            headers=resp_headers,
            content=content,
            content_type=content_type,
            canonical_url=canonical_url,
        )
    finally:
        if own_client:
            await client.aclose()

