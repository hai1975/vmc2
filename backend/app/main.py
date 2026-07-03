from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.database import init_db
from app.routers import forms, mc, sessions, settings


class StripMountPathMiddleware:
    """Strip cPanel subfolder prefix (e.g. /vmc-api) when Passenger forwards full path."""

    def __init__(self, app: ASGIApp, mount_path: str) -> None:
        self.app = app
        self.prefix = mount_path.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and self.prefix:
            path = scope.get("path", "")
            if path == self.prefix or path.startswith(f"{self.prefix}/"):
                scope = dict(scope)
                scope["path"] = path[len(self.prefix) :] or "/"
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


mount = settings.api_mount_path.strip() or None
app = FastAPI(
    title="VM Clinic Form Assistant API",
    version="0.1.0",
    lifespan=lifespan,
    root_path=mount or "",
)

if mount:
    app.add_middleware(StripMountPathMiddleware, mount_path=mount)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forms.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(mc.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "vm-clinic-api",
        "gemini_configured": bool(settings.gemini_api_key),
    }
