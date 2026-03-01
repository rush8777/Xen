from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .models import *  # noqa: F401,F403 - register models
from .routers import internal_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm Cobalt rotator so first ingest request on a fresh Cloud Run instance
    # doesn't pay instance-probing latency.
    from .cobalt_downloader import warm_up_rotator

    await warm_up_rotator()
    yield


def create_worker_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    app = FastAPI(title="v0-social Worker", version="0.1.0", lifespan=lifespan)
    app.include_router(internal_tasks.router)
    return app


app = create_worker_app()
