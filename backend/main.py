from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from fastapi import BackgroundTasks

from .config import settings

from .database import Base, engine

from .models import *  # Import all models to register them with SQLAlchemy

from .routers import oauth, connections, videos, analysis, projects, chats
from .routers import project_statistics
from .routers import project_overview
from .routers import premium_analysis
from .routers import project_content_features
from .routers import project_psychology





@asynccontextmanager
async def lifespan(app: FastAPI):
    from .cobalt_downloader import warm_up_rotator
    await warm_up_rotator()
    yield


def create_app() -> FastAPI:

    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="v0-social Backend", version="0.1.0", lifespan=lifespan)



    origins = [

        settings.FRONTEND_BASE_URL,

        "http://localhost:3000",

        "http://127.0.0.1:3000",

    ]



    app.add_middleware(

        CORSMiddleware,

        allow_origins=origins,

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],

    )



    app.include_router(oauth.router)

    app.include_router(connections.router)

    app.include_router(videos.router)

    app.include_router(analysis.router)

    app.include_router(projects.router)

    app.include_router(project_statistics.router)

    app.include_router(project_overview.router)

    app.include_router(premium_analysis.router)
    app.include_router(project_content_features.router)
    app.include_router(project_psychology.router)

    app.include_router(chats.router)



    return app





app = create_app()





