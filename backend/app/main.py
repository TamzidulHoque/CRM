from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import main as legacy_main
from user_location import get_current_location

from .db import get_db
from .models import RegisteredClinic
from .settings import get_settings


class LegacySearchRequest(BaseModel):
    keyword: str | None = None


class RegisteredClinicOut(BaseModel):
    id: UUID
    place_id: str | None
    name: str
    created_at: datetime


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

    @app.get("/clinics", include_in_schema=False)
    async def clinics_page() -> FileResponse:
        return FileResponse(static_dir / "clinics.html")

    @app.post("/api/legacy-search")
    def legacy_search(payload: LegacySearchRequest) -> dict[str, str]:
        """Call the existing run_system() using only the detected IP-based location."""
        keyword = payload.keyword or "Dermal fillers"

        lat, lng = get_current_location()
        if not lat or not lng:
            raise HTTPException(status_code=500, detail="Location detection failed")

        try:
            legacy_main.run_system(lat, lng, keyword)
        except Exception as exc:  # pragma: no cover - legacy script errors surfaced to client
            raise HTTPException(status_code=500, detail=f"Legacy search failed: {exc}") from exc

        return {"status": "ok"}

    @app.get("/api/clinics/registered", response_model=list[RegisteredClinicOut])
    async def list_registered_clinics(
        db: AsyncSession = Depends(get_db),
    ) -> list[RegisteredClinicOut]:
        try:
            result = await db.execute(select(RegisteredClinic).order_by(RegisteredClinic.created_at.desc()))
            clinics = result.scalars().all()
            return [RegisteredClinicOut.model_validate(c) for c in clinics]
        except Exception:
            # If the database is not reachable yet, treat as "no clinics"
            return []

    return app


app = create_app()

