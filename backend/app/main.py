from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import main as legacy_main
from user_location import get_current_location

from .settings import get_settings


class LegacySearchRequest(BaseModel):
    keyword: str | None = None


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    base_dir = Path(__file__).resolve().parent
    static_dir = base_dir / "static"

    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.post("/api/legacy-search")
    def legacy_search(payload: LegacySearchRequest) -> dict[str, str]:
        lat, lng = get_current_location()
        if not lat or not lng:
            raise HTTPException(status_code=500, detail="Location detection failed")

        keyword = payload.keyword or "Dermal fillers"
        legacy_main.run_system(lat, lng, keyword)
        return {"status": "ok"}

    return app


app = create_app()

