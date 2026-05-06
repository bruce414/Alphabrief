"""YouTube metadata (oEmbed) and transcript helpers."""

from __future__ import annotations

import asyncio
import re
from urllib.parse import parse_qs, urlparse

import httpx
import requests

from app.core.config import Settings, get_settings


def parse_youtube_video_id(url: str) -> str | None:
    p = urlparse(url.strip())
    host = (p.hostname or "").lower()
    path = p.path or ""

    if host in {"youtu.be", "www.youtu.be"}:
        vid = path.strip("/").split("/")[0]
        return vid or None

    if "youtube.com" in host or "youtube-nocookie.com" in host:
        qs = parse_qs(p.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
        m = re.search(r"/embed/([^/?]+)", path)
        if m:
            return m.group(1)
        m = re.search(r"/shorts/([^/?]+)", path)
        if m:
            return m.group(1)
        m = re.search(r"/live/([^/?]+)", path)
        if m:
            return m.group(1)
    return None


def _is_youtube_url(url: str) -> bool:
    try:
        p = urlparse(url.strip())
    except Exception:
        return False
    host = (p.hostname or "").lower()
    return (
        "youtube.com" in host
        or "youtu.be" in host
        or "youtube-nocookie.com" in host
    )


async def fetch_oembed(
    watch_url: str,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict:
    settings = settings or get_settings()
    timeout = httpx.Timeout(settings.fetch_timeout_seconds)
    own = client is None
    client = client or httpx.AsyncClient(timeout=timeout, trust_env=False)
    try:
        r = await client.get(
            "https://www.youtube.com/oembed",
            params={"url": watch_url, "format": "json"},
            headers={"User-Agent": settings.http_user_agent},
        )
        r.raise_for_status()
        return r.json()
    finally:
        if own:
            await client.aclose()


async def fetch_transcript_text(
    video_id: str,
) -> str | None:
    """Returns joined transcript text or None if unavailable."""

    def _sync() -> str | None:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # `youtube-transcript-api` uses `requests` under the hood which will
            # inherit proxy env vars by default. In some environments that causes:
            # "Tunnel connection failed: 403 Forbidden".
            s = requests.Session()
            s.trust_env = False
            api = YouTubeTranscriptApi(http_client=s)
            transcript_list = api.list(video_id)

            # Prefer manually created English, then generated English, then anything.
            chunks = None
            for lang in ("en", "en-US", "en-GB"):
                try:
                    chunks = (
                        transcript_list.find_manually_created_transcript([lang])
                        .fetch()
                    )
                    break
                except Exception:
                    pass
                try:
                    chunks = transcript_list.find_generated_transcript([lang]).fetch()
                    break
                except Exception:
                    pass
            if chunks is None:
                chunks = next(iter(transcript_list)).fetch()
        except Exception:
            return None
        # youtube-transcript-api returns typed snippet objects (not dicts).
        parts = [getattr(c, "text", "") for c in chunks]
        return "\n".join(p for p in parts if p).strip() or None

    return await asyncio.to_thread(_sync)
