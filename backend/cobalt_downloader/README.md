# Cobalt Video Downloader — Drop-in Backend

Uses [Cobalt](https://cobalt.tools) as the download engine.  
Supports **YouTube, Facebook, Instagram, TikTok, Twitter/X, Reddit, Twitch, Vimeo, Dailymotion, Bilibili, SoundCloud** and more — with no binaries required.

---

## Files in this package

| File | Purpose |
|---|---|
| `cobalt_downloader.py` | `VideoDownloader` class — identical API to the original |
| `cobalt_instances.py` | Instance list + async latency tester + `CobaltInstanceRotator` |
| `worker_tasks.py` | Your original worker file with **one line changed** |
| `main.py` | Your original CLI with **one line changed** |
| `Dockerfile` | Cloud Run-optimised image (no ffmpeg required) |
| `requirements.txt` | Updated deps |

---

## How to integrate (plug-and-play)

### Step 1 — Copy the package into your project

Place the `cobalt_downloader/` folder alongside your existing modules:

```
your_project/
├── app/
│   ├── cobalt_downloader/       ← NEW (this package)
│   │   ├── __init__.py
│   │   ├── cobalt_downloader.py
│   │   ├── cobalt_instances.py
│   │   ├── main.py
│   │   └── worker_tasks.py
│   ├── routers/
│   ├── models.py
│   └── ...
```

### Step 2 — Update the import in worker_tasks.py

```python
# Before
from ..routers.video_downloader import VideoDownloader

# After (already done in the provided worker_tasks.py)
from ..cobalt_downloader import VideoDownloader
```

That's the only required change. The `VideoDownloader` class has the exact same interface:
- `__init__(download_dir)`
- `download(url, quality, audio_only, output_filename) → str`
- `get_info(url) → dict`
- `get_supported_platforms() → list`
- `download_dir` attribute (reassignable — worker_tasks.py does this for /tmp)

### Step 3 — Warm up the rotator at startup (recommended for Cloud Run)

In your FastAPI app entry point:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.cobalt_downloader import warm_up_rotator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Probes all Cobalt instances and ranks them by latency.
    # Runs once at startup so the first real download is instant.
    await warm_up_rotator()
    yield

app = FastAPI(lifespan=lifespan)
```

---

## Instance rotation explained

`CobaltInstanceRotator` keeps a **latency-ranked list** of live instances:

```
RANK   LATENCY   VERSION       AUTH    URL
★ 1    112 ms    10.3.2        open    https://dwnld.nichind.dev
★ 2    189 ms    10.3.1        open    https://cobalt.canine.tools
  3    244 ms    10.3.0        open    https://cobalt.meowing.de
  ...
  ✗    https://cobalt.synzr.space   Timeout
```

- **On each download**, `get_best()` returns the fastest healthy instance.
- **On failure**, `mark_failed(url)` deprioritises that instance.
- **After 3 consecutive failures**, the instance is skipped automatically.
- **If all instances fail**, the rotator refreshes (re-probes) and tries again.
- **Refresh cadence**: automatically triggered when the list is exhausted.  
  You can also call `rotator.refresh_async()` on a schedule (e.g. every 10 min).

---

## Quality mapping

| Your param | Cobalt quality |
|---|---|
| `best`  | `max` |
| `1080p` | `1080` |
| `720p`  | `720` |
| `480p`  | `480` |
| `360p`  | `360` |
| `240p`  | `240` |
| `144p`  | `144` |

---

## Cloud Run notes

- **No ffmpeg** — Cobalt handles all transcoding server-side. The Docker image is ~180 MB vs ~600 MB+ with ffmpeg.
- **No legacy downloader dependency** in this package.
- **`/tmp` writes** — Cloud Run has a 512 MB in-memory `/tmp`. The worker already redirects downloads there; files are cleaned up after upload to Gemini.
- **Concurrency** — `aiohttp` + `asyncio.gather` means parallel downloads don't block each other. Cloud Run scales horizontally; the rotator is per-instance (stateless, no shared state needed).
- **SSL** — `ssl=False` in the `TCPConnector` avoids certificate chain issues on some Cloud Run environments. The Cobalt instances are still contacted over HTTPS.

---

## Supported platforms (Cobalt)

YouTube · Facebook · Instagram · TikTok · Twitter/X · Reddit · Twitch ·  
Vimeo · Dailymotion · Bilibili · SoundCloud · Pinterest · Rumble ·  
Odysee · Loom · OK.ru · VK · Niconico · Streamable · Vine (archive)

Full list: https://github.com/imputnet/cobalt

---

## Self-hosting Cobalt (recommended for production)

Public instances are community-run and may go offline. For a production service,
self-hosting takes ~5 minutes with Docker:

```bash
docker run -p 9000:9000 ghcr.io/imputnet/cobalt:latest
```

Then pass your instance URL:
```python
from app.cobalt_downloader.cobalt_instances import CobaltInstanceRotator
rotator = CobaltInstanceRotator(instances=["https://your-cobalt.example.com"])
```

Guide: https://github.com/imputnet/cobalt/blob/main/docs/run-an-instance.md
