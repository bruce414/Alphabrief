"""Basic SSRF protections before fetching user-supplied URLs."""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from urllib.parse import urlparse, urlunparse

from fastapi import status

from app.core.config import Settings, get_settings
from app.core.errors import AppError

_LOCALHOST_LABELS = frozenset(
    {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "invalid",
    }
)


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    if addr.version == 4:
        return bool(
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_multicast
            or addr.is_reserved
            or addr.is_unspecified
        )
    # IPv6
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _hostname_is_localhost_pattern(hostname: str) -> bool:
    h = hostname.strip().lower().rstrip(".")
    if h in _LOCALHOST_LABELS:
        return True
    if h.endswith(".localhost") or h.endswith(".local"):
        return True
    if re.match(r"^127\.\d+\.\d+\.\d+$", h):
        return True
    return False


def _hostname_matches_denylist(hostname: str, settings: Settings) -> bool:
    h = hostname.strip().lower().rstrip(".")
    for suf in settings.source_domain_denylist_suffixes():
        s = suf.lower().lstrip(".")
        if not s:
            continue
        if h == s or h.endswith(f".{s}"):
            return True
    return False


def assert_url_scheme_http(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise AppError(
            error_code="INVALID_URL",
            message="Only http and https URLs are allowed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not parsed.netloc:
        raise AppError(
            error_code="INVALID_URL",
            message="URL is missing a host",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def resolve_host_ips(hostname: str) -> list[str]:
    """Resolve all A/AAAA records; returns IP strings."""
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise AppError(
            error_code="INVALID_URL",
            message="Could not resolve hostname",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    ips: list[str] = []
    seen: set[str] = set()
    for info in infos:
        sockaddr = info[4]
        # Typeshed can surface this as `str | int` depending on sockaddr variants.
        # We only care about IP-like string forms here.
        ip = str(sockaddr[0])
        if ip not in seen:
            seen.add(ip)
            ips.append(ip)
    return ips


async def validate_http_url_safe_for_fetch(url: str, *, settings: Settings | None = None) -> str:
    """Validate scheme/host/DNS; raise AppError if blocked or unsafe."""
    settings = settings or get_settings()
    assert_url_scheme_http(url)
    parsed = urlparse(url)
    host = parsed.hostname
    if host is None:
        raise AppError(
            error_code="INVALID_URL",
            message="URL is missing a host",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if _hostname_is_localhost_pattern(host):
        raise AppError(
            error_code="SOURCE_BLOCKED",
            message="Localhost targets are not allowed",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if _hostname_matches_denylist(host, settings):
        raise AppError(
            error_code="SOURCE_BLOCKED",
            message="This domain is blocked by policy",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Literal IP in URL
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if _is_blocked_ip(host):
            raise AppError(
                error_code="SOURCE_BLOCKED",
                message="Private or blocked IP targets are not allowed",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return url

    def _resolve() -> None:
        ips = resolve_host_ips(host)
        if not ips:
            raise AppError(
                error_code="INVALID_URL",
                message="Could not resolve hostname",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        for ip in ips:
            if _is_blocked_ip(ip):
                raise AppError(
                    error_code="SOURCE_BLOCKED",
                    message="Hostname resolves to a private or blocked address",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

    await asyncio.to_thread(_resolve)
    return url


def normalize_http_url(url: str) -> str:
    """Best-effort canonical form for storage (strip fragments)."""
    p = urlparse(url)
    cleaned = p._replace(fragment="")
    return urlunparse(cleaned)
