import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import APP_NAME, settings
from app.db import initialize_database
from app.routers import qa, translate, video
from app.sessions import SessionMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title=f"{APP_NAME} API", lifespan=lifespan)

app.add_middleware(SessionMiddleware)

if settings.is_dev and settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(video.router)
app.include_router(video.sse_router)
app.include_router(qa.router)
app.include_router(translate.router)


_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "out")

if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
else:

    @app.get("/")
    async def frontend_missing():
        return {"detail": "frontend build missing", "api_docs": "/docs"}
