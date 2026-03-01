"""
cobalt_downloader.py
=====================
Drop-in replacement for the legacy VideoDownloader class.

CONTRACT — identical public interface to the original VideoDownloader:
  • __init__(download_dir)
  • download(url, quality, audio_only, output_filename) -> str   (filepath)
  • get_info(url) -> dict
  • get_supported_platforms() -> list[str]
  • download_dir  (Path attribute, reassignable — worker_tasks.py does this)

Additional capabilities:
  • Cobalt backend — supports YouTube, Facebook, Instagram, TikTok, Twitter/X,
    Reddit, Twitch, Vimeo, Dailymotion, Bilibili, Pinterest, SoundCloud, etc.
  • Automatic instance rotation with latency-ranked fallback.
  • async-native download; sync wrapper keeps callers unchanged.
  • No ffmpeg required (Cobalt handles transcoding server-side).
  • Cloud Run friendly: no binary deps, no cookies, no cookies.txt.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Optional

import aiohttp

from .cobalt_instances import CobaltInstanceRotator

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Single instance URL - no rotation needed
# ─────────────────────────────────────────────────────────────────────────────
_SINGLE_INSTANCE = "https://dwnld.nichind.dev"


# ─────────────────────────────────────────────────────────────────────────────
# Quality mapping  (our labels → Cobalt videoQuality param)
# Cobalt accepts: "max", "2160", "1440", "1080", "720", "480", "360", "240", "144"
# ─────────────────────────────────────────────────────────────────────────────
_QUALITY_MAP: dict[str, str] = {
    "best":  "max",
    "2160p": "2160",
    "1440p": "1440",
    "1080p": "1080",
    "720p":  "720",
    "480p":  "480",
    "360p":  "360",
    "240p":  "240",
    "144p":  "144",
}

_DOWNLOAD_TIMEOUT_S = 300   # 5 min for actual file download
_API_TIMEOUT_S      = 30    # timeout for Cobalt API call
_MAX_RETRIES        = 3     # how many different instances to try per download


class VideoDownloader:
    """
    Cobalt-backed video downloader.
    Identical public interface to the original VideoDownloader so
    worker_tasks.py and main.py need zero changes.
    """

    def __init__(self, download_dir: str = "./downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def download(
        self,
        url: str,
        quality: str = "best",
        audio_only: bool = False,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        Download a video/audio file via Cobalt and return its local filepath.
        Sync wrapper — safe to call from any thread or worker task.
        """
        return _run_sync(self._download_async(url, quality, audio_only, output_filename))

    def get_info(self, url: str) -> Dict:
        """
        Return a metadata dict that mirrors the previous info dict shape.
        Fields that Cobalt doesn't provide are filled with sensible defaults
        so downstream code that reads e.g. info['title'] still works.
        """
        return _run_sync(self._get_info_async(url))

    def get_supported_platforms(self) -> list:
        return [
            "YouTube", "Facebook", "Instagram", "TikTok", "Twitter/X",
            "Reddit", "Twitch", "Vimeo", "Dailymotion", "Bilibili",
            "Pinterest", "SoundCloud", "Vine", "Streamable", "Rumble",
            "Odysee", "Loom", "OK.ru", "VK", "Niconico",
            # Cobalt supports ~30+ platforms — this is the notable subset
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # Internal async implementation
    # ─────────────────────────────────────────────────────────────────────────

    async def _download_async(
        self,
        url: str,
        quality: str = "best",
        audio_only: bool = False,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        Core async download logic with single instance.
        Tries up to _MAX_RETRIES before raising.
        """
        cobalt_quality = _QUALITY_MAP.get(quality, "720")

        for attempt in range(_MAX_RETRIES):
            logger.info("Download attempt %d/%d via %s", attempt + 1, _MAX_RETRIES, _SINGLE_INSTANCE)

            try:
                filepath = await self._download_from_instance(
                    instance=_SINGLE_INSTANCE,
                    url=url,
                    cobalt_quality=cobalt_quality,
                    audio_only=audio_only,
                    output_filename=output_filename,
                )
                return filepath

            except CobaltAPIError as exc:
                # API-level error (bad URL, unsupported platform, rate limit)
                logger.error("Cobalt API error from %s: %s", _SINGLE_INSTANCE, exc)
                raise

            except Exception as exc:
                logger.warning("Instance %s failed: %s — retrying", _SINGLE_INSTANCE, exc)
                if attempt == _MAX_RETRIES - 1:
                    raise exc
                continue

        raise RuntimeError(
            f"All {_MAX_RETRIES} Cobalt instance attempts failed for {url}"
        )

    async def _download_from_instance(
        self,
        instance: str,
        url: str,
        cobalt_quality: str,
        audio_only: bool,
        output_filename: Optional[str],
    ) -> str:
        """Single-instance download attempt."""
        url = _clean_url(url)                                      # ← add
        logger.info("Sending to Cobalt: %s", url)                  # ← add
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:

            # ── Step 1: ask Cobalt for the download URL ───────────────────
            payload: dict = {
                "url": url,
                "videoQuality": "360",
                "audioFormat": "mp3" ,
                "filenameStyle": "pretty",
            }
            if audio_only:
                payload["downloadMode"] = "audio"

            api_timeout = aiohttp.ClientTimeout(total=_API_TIMEOUT_S)
            try:
                async with session.post(
                    f"{instance}/",
                    json=payload,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    timeout=api_timeout,
                ) as resp:
                    raw_text = await resp.text()
            except aiohttp.ClientError as exc:
                raise ConnectionError(f"API call failed: {exc}") from exc

            if resp.status >= 400:
                raise RuntimeError(f"Cobalt API HTTP {resp.status}: {raw_text[:200]}")

            try:
                data = json.loads(raw_text) if raw_text else {}
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Cobalt API returned non-JSON payload: {raw_text[:200]}") from exc

            if not isinstance(data, dict):
                raise RuntimeError(f"Cobalt API returned unexpected payload type: {type(data).__name__}")

            status = data.get("status", "")
            logger.debug("Cobalt API response status: %s", status)

            if status == "error":
                error_obj = data.get("error")
                if isinstance(error_obj, dict):
                    code = error_obj.get("code") or error_obj.get("message")
                    if code:
                        raise CobaltAPIError(str(code))
                if isinstance(error_obj, str) and error_obj.strip():
                    raise CobaltAPIError(error_obj.strip())
                raise RuntimeError("Cobalt API returned status=error with malformed error payload")

            if status == "picker":
                # Multi-item response (e.g. Instagram carousel)
                # Download the first item — caller can handle picker items separately
                items = data.get("picker", [])
                if not items:
                    raise CobaltAPIError("picker_empty")
                first_item = items[0]
                if not isinstance(first_item, dict) or not first_item.get("url"):
                    raise RuntimeError("Cobalt picker payload missing item URL")
                download_url = first_item["url"]
                server_filename = first_item.get("filename") or _url_to_filename(download_url, audio_only)
                logger.info("Picker response — downloading first item: %s", download_url)

            elif status in ("tunnel", "redirect"):
                download_url = data["url"]
                server_filename = data.get("filename") or _url_to_filename(download_url, audio_only)

            else:
                raise CobaltAPIError(f"unexpected_status:{status}")

            # ── Step 2: resolve local output path ─────────────────────────
            if output_filename:
                ext = Path(server_filename).suffix or (".mp3" if audio_only else ".mp4")
                local_path = self.download_dir / f"{_sanitize(output_filename)}{ext}"
            else:
                local_path = self.download_dir / _sanitize(server_filename)

            # ── Step 3: stream the file to disk ───────────────────────────
            dl_timeout = aiohttp.ClientTimeout(total=_DOWNLOAD_TIMEOUT_S)
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=dl_timeout,
            ) as dl_session:
                async with dl_session.get(download_url, allow_redirects=True) as file_resp:
                    file_resp.raise_for_status()
                    total = int(file_resp.headers.get("Content-Length", 0))
                    downloaded = 0

                    with open(local_path, "wb") as fh:
                        async for chunk in file_resp.content.iter_chunked(1024 * 256):
                            fh.write(chunk)
                            downloaded += len(chunk)
                            if total:
                                pct = downloaded / total * 100
                                print(f"\rDownloading: {pct:.1f}%", end="", flush=True)

            print(f"\n✓ Download finished: {local_path}")
            return str(local_path)

    async def _get_info_async(self, url: str) -> Dict:
        """
        Returns a compatible info dict.
        Cobalt doesn't have a dedicated metadata endpoint so we do a dry-run
        API call and normalise the response into the expected shape.
        """
        payload = {
            "url": url,
            "videoQuality": "max",
            "filenameStyle": "pretty",
        }

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            timeout = aiohttp.ClientTimeout(total=_API_TIMEOUT_S)
            async with session.post(
                f"{_SINGLE_INSTANCE}/",
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=timeout,
            ) as resp:
                raw_text = await resp.text()

        if resp.status >= 400:
            raise RuntimeError(f"Cobalt info API HTTP {resp.status}: {raw_text[:200]}")

        try:
            data = json.loads(raw_text) if raw_text else {}
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Cobalt info API returned non-JSON payload: {raw_text[:200]}") from exc

        if not isinstance(data, dict):
            raise RuntimeError(f"Cobalt info API returned unexpected payload type: {type(data).__name__}")

        # Build a compatible info dict from whatever Cobalt gives us
        filename = data.get("filename", "")
        title = _filename_to_title(filename) or _extract_title_from_url(url)
        platform = _detect_platform(url)

        info: Dict = {
            "title":       title,
            "url":         url,
            "extractor":   platform,
            "uploader":    None,
            "duration":    None,
            "view_count":  None,
            "formats":     [],
            # Cobalt-specific extras
            "_cobalt": {
                "status":   data.get("status"),
                "instance": _SINGLE_INSTANCE,
            },
        }

        # If Cobalt gave us a direct download URL, add a pseudo-format entry
        if data.get("status") in ("tunnel", "redirect") and data.get("url"):
            info["formats"] = [{
                "format_id":  "cobalt-best",
                "url":        data["url"],
                "ext":        Path(filename).suffix.lstrip(".") or "mp4",
                "resolution": "N/A",
                "format_note": "best available via Cobalt",
                "filesize":   None,
            }]

        return info


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class CobaltAPIError(Exception):
    """Raised when Cobalt returns a well-formed error response."""


def _run_sync(coro) -> any:
    """
    Run a coroutine from sync code.
    Works in plain threads, Cloud Run workers, and Jupyter/Colab
    (where an event loop is already running).
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop and running_loop.is_running():
        import nest_asyncio  # type: ignore
        nest_asyncio.apply()
        return running_loop.run_until_complete(coro)

    # No running loop in this thread (typical worker thread case on Python 3.12+)
    return asyncio.run(coro)


def _sanitize(name: str) -> str:
    """Remove characters that are unsafe in filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name.strip()[:200]


def _url_to_filename(url: str, audio_only: bool) -> str:
    """Derive a filename from a URL when Cobalt doesn't supply one."""
    path = urllib.parse.urlparse(url).path
    base = Path(path).name or "video"
    if not Path(base).suffix:
        base += ".mp3" if audio_only else ".mp4"
    return base


def _filename_to_title(filename: str) -> str:
    """Convert a pretty filename like 'Artist - Song (720p).mp4' to a title."""
    stem = Path(filename).stem
    # Remove trailing quality/resolution tags like (720p), [1080p], etc.
    stem = re.sub(r'[\[(]\d{3,4}p[\])]', "", stem).strip()
    return stem


def _extract_title_from_url(url: str) -> str:
    """Last-resort title extraction from the URL itself."""
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if "v" in qs:
        return f"YouTube video {qs['v'][0]}"
    return parsed.netloc + parsed.path


def _detect_platform(url: str) -> str:
    """Map URL to a platform name."""
    host = urllib.parse.urlparse(url).netloc.lower()
    mapping = {
        "youtube.com": "YouTube", "youtu.be": "YouTube",
        "facebook.com": "Facebook", "fb.com": "Facebook", "fb.watch": "Facebook",
        "instagram.com": "Instagram",
        "tiktok.com": "TikTok",
        "twitter.com": "Twitter", "x.com": "Twitter",
        "reddit.com": "Reddit",
        "twitch.tv": "Twitch",
        "vimeo.com": "Vimeo",
        "dailymotion.com": "Dailymotion",
        "bilibili.com": "Bilibili",
        "soundcloud.com": "SoundCloud",
        "pinterest.com": "Pinterest",
        "rumble.com": "Rumble",
        "odysee.com": "Odysee",
        "ok.ru": "OK.ru",
        "vk.com": "VK",
        "nicovideo.jp": "Niconico",
    }
    for domain, name in mapping.items():
        if domain in host:
            return name
    return "Unknown"


def _clean_url(url: str) -> str:
    """Strip tracking params that confuse Cobalt."""
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)

    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        qs = {k: v for k, v in qs.items() if k in ("v", "list", "t")}

    clean = parsed._replace(query=urllib.parse.urlencode(qs, doseq=True))
    return urllib.parse.urlunparse(clean)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level startup helper
# ─────────────────────────────────────────────────────────────────────────────

async def warm_up_rotator() -> None:
    """
    No-op function for compatibility.
    Single instance doesn't need warm-up.
    """
    logger.info("Using single Cobalt instance: %s", _SINGLE_INSTANCE)
    # No warm-up needed for single instance
