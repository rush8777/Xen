# Extractor (Cobalt-only)

This extractor path is now Cobalt-only.

- Video download adapters forward to `backend.cobalt_downloader.VideoDownloader`.
- Comment extraction is intentionally disabled in this runtime.
- Cloud Run workers and API use the Cobalt downloader path.
