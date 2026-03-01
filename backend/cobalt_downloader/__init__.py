"""
cobalt_downloader package
=========================
Drop-in Cobalt-backed replacement for the legacy video downloader.

Quick start
-----------
Replace your import:

    # Before:
    from video_downloader.downloader import VideoDownloader
    # or
    from video_downloader.video_downloader import VideoDownloader

    # After (one-line change):
    from video_downloader.cobalt_downloader import VideoDownloader

That's it. The class contract is identical.

For Cloud Run / FastAPI — hook into lifespan startup to pre-warm instances:

    from video_downloader.cobalt_downloader import warm_up_rotator

    @asynccontextmanager
    async def lifespan(app):
        await warm_up_rotator()
        yield

    app = FastAPI(lifespan=lifespan)
"""

from .cobalt_downloader import VideoDownloader, warm_up_rotator, CobaltAPIError
from .cobalt_instances import CobaltInstanceRotator, COBALT_INSTANCES

__all__ = [
    "VideoDownloader",
    "warm_up_rotator",
    "CobaltAPIError",
    "CobaltInstanceRotator",
    "COBALT_INSTANCES",
]
