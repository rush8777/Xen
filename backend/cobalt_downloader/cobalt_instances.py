"""
cobalt_instances.py
====================
Curated list of public Cobalt API instances + async latency tester + rotator.

The CobaltInstanceRotator is the main class consumed by VideoDownloader.
It is safe to instantiate once at module level (singleton pattern) â€” the
VideoDownloader does exactly that so every request shares the same ranked list.

NOTE: Call rotator.refresh() once at startup (e.g. in a FastAPI lifespan hook).
      The ranked list is cached in memory; call refresh() periodically or
      whenever get_best() returns None to rebuild it.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Curated instance list
# Sources: instances.cobalt.best, cobalt.directory, community reports (Feb 2025)
# Instances may come and go â€” the tester will weed out dead ones automatically.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
COBALT_INSTANCES: list[str] = [
    "https://dwnld.nichind.dev",
    "https://cobalt.api.timelessnesses.me",
    "https://cobalt.canine.tools",
    "https://cobalt.meowing.de",
    "https://capi.oak.li",
    "https://cobalt.synzr.space",
    "https://api-dl.cgm.rs",
    "https://co.tskau.team",
    "https://cobalt.ggtyler.dev",
    "https://dl.co.anax.cc",
    "https://cobalt.prixyflare.pro",
    "https://cblt.fariz.dev",
    "https://cobalt.pabloantunes.com",
    "https://cobalt.privacyredirect.com",
    "https://cobalt.lunar.icu",
    "https://cobalt.nadeko.net",
    "https://cobalt.tux.pizza",
    "https://cobalt.bloatcat.net",
    "https://dl.stardust.moe",
    "https://cobalt.api.lissy.dev",
    "https://cobalt.nite.lol",
    "https://cobalt.drgns.space",
    "https://cobalt.freestuff.dev",
    "https://dl.roh.tf",
]

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Tester config
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_TIMEOUT_S   = 8    # per-instance timeout for the health probe
_PING_ROUNDS = 2    # how many rounds to average latency over (keep low at startup)
_MAX_FAILURES = 3   # consecutive failures before an instance is skipped


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Low-level async probe
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async def _probe_instance(session: aiohttp.ClientSession, url: str) -> dict:
    """
    Hits GET {url}/ and returns a result dict:
      online, latency_ms, cobalt_version, requires_auth, error
    """
    result: dict = {
        "url": url,
        "online": False,
        "latency_ms": None,
        "cobalt_version": None,
        "requires_auth": False,
        "error": None,
    }
    latencies: list[float] = []

    for _ in range(_PING_ROUNDS):
        t0 = time.perf_counter()
        try:
            async with session.get(
                f"{url}/",
                headers={"Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=_TIMEOUT_S),
                allow_redirects=True,
            ) as resp:
                elapsed_ms = (time.perf_counter() - t0) * 1000

                if resp.status in (401, 403):
                    result["requires_auth"] = True
                    result["error"] = f"HTTP {resp.status} â€” auth required"
                    latencies.append(elapsed_ms)
                    continue

                if resp.status != 200:
                    result["error"] = f"HTTP {resp.status}"
                    break

                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {}

                version = data.get("cobalt", {}).get("version") or data.get("version")
                if version:
                    result["cobalt_version"] = version

                latencies.append(elapsed_ms)

        except asyncio.TimeoutError:
            result["error"] = "Timeout"
            break
        except aiohttp.ClientConnectorError as exc:
            result["error"] = f"Connection error: {exc}"
            break
        except Exception as exc:
            result["error"] = str(exc)
            break

    if latencies:
        result["online"] = True
        result["latency_ms"] = round(sum(latencies) / len(latencies), 1)

    return result


async def _run_all_probes(instances: list[str]) -> list[dict]:
    """Probes all instances concurrently, returns sorted results."""
    # ssl=False avoids cert-chain issues on some Cloud Run / Colab environments
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await asyncio.gather(*[_probe_instance(session, url) for url in instances])

    results = list(results)
    results.sort(key=lambda r: (
        0 if r["online"] else 1,
        r["latency_ms"] if r["latency_ms"] is not None else float("inf"),
    ))
    return results


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Public rotator â€” consumed by VideoDownloader
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class CobaltInstanceRotator:
    """
    Thread-safe(ish) rotator that keeps a ranked list of working Cobalt instances.

    Lifecycle (plug-and-play):
      1. Instantiate once at module level (see cobalt_downloader.py).
      2. Call await rotator.refresh_async() inside an async startup hook, OR
         call rotator.refresh_sync() from sync code (e.g. a background thread).
      3. Call rotator.get_best() to get the fastest open instance URL.
      4. After each download, call mark_success(url) or mark_failed(url).
    """

    def __init__(self, instances: list[str] = COBALT_INSTANCES):
        self._all = list(instances)
        self._ranked: list[dict] = []
        self._failures: dict[str, int] = {}

    # â”€â”€ refresh â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def refresh_async(self) -> list[dict]:
        """Async refresh â€” use inside FastAPI lifespan or async context."""
        logger.info("CobaltInstanceRotator: probing %d instancesâ€¦", len(self._all))
        self._ranked = await _run_all_probes(self._all)
        self._failures = {}
        online = [r for r in self._ranked if r["online"] and not r["requires_auth"]]
        logger.info(
            "CobaltInstanceRotator: %d/%d instances online. Best: %s (%.0f ms)",
            len(online), len(self._all),
            online[0]["url"] if online else "none",
            online[0]["latency_ms"] if online else 0,
        )
        return self._ranked

    def refresh_sync(self) -> list[dict]:
        """Sync refresh — creates its own event loop. Use in worker threads."""
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop and running_loop.is_running():
            # We're inside an existing loop (e.g. Jupyter / Colab)
            import nest_asyncio  # type: ignore
            nest_asyncio.apply()
            return running_loop.run_until_complete(self.refresh_async())

        return asyncio.run(self.refresh_async())

    # â”€â”€ selection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def get_best(self, skip_auth_required: bool = True) -> Optional[str]:
        """Return the URL of the best currently healthy instance, or None."""
        for r in self._ranked:
            if not r["online"]:
                break  # remaining are also offline (list is sorted)
            if skip_auth_required and r["requires_auth"]:
                continue
            if self._failures.get(r["url"], 0) >= _MAX_FAILURES:
                continue
            return r["url"]
        return None

    def get_ranked_urls(self, online_only: bool = True, skip_auth: bool = True) -> list[str]:
        """Flat list of instance URLs in rank order."""
        return [
            r["url"] for r in self._ranked
            if (not online_only or r["online"])
            and (not skip_auth or not r["requires_auth"])
        ]

    # â”€â”€ feedback â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def mark_failed(self, url: str) -> None:
        """Deprioritise an instance after a download error."""
        self._failures[url] = self._failures.get(url, 0) + 1
        logger.warning(
            "CobaltInstanceRotator: marked %s as failed (%d consecutive)",
            url, self._failures[url],
        )

    def mark_success(self, url: str) -> None:
        """Reset failure counter after a successful download."""
        self._failures[url] = 0

    # â”€â”€ diagnostics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def print_status(self) -> None:
        """Pretty-print current ranked list (useful for debugging)."""
        print(f"\n{'='*70}")
        print(f"{'RANK':<5} {'LATENCY':>9}  {'VERSION':<12}  {'AUTH':<5}  URL")
        print(f"{'='*70}")
        rank = 0
        for r in self._ranked:
            if not r["online"]:
                continue
            rank += 1
            auth = "ðŸ”’" if r["requires_auth"] else "open"
            print(f"{'â˜… ' if rank <= 5 else '  '}{rank:<3} {r['latency_ms']:>6.0f} ms  "
                  f"{(r['cobalt_version'] or 'unknown'):<12}  {auth:<5}  {r['url']}")
        offline = [r for r in self._ranked if not r["online"]]
        if offline:
            print(f"\nâ”€â”€ Offline ({len(offline)}) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
            for r in offline:
                print(f"  âœ—  {r['url']:<50}  {r['error']}")
        print(f"{'='*70}\n")

