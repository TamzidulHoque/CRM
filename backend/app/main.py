from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Clinic
from .settings import get_settings

from .db import get_db

# Lazy imports for legacy modules - wrapped in try/except to allow app to start
# we log errors here so that startup failures are visible in the server logs.
import logging

logger = logging.getLogger(__name__)


def _get_legacy_main():
    try:
        # The legacy orchestration entrypoint lives in `operations.py`.
        # `main.py` in the repo is a small CLI wrapper and does not expose `run_system`,
        # so importing it here causes runtime failures.
        import operations as legacy_ops
        return legacy_ops
    except Exception as e:
        logger.exception("unable to import legacy main module")
        raise ImportError(f"Failed to import legacy main module: {e}")

def _get_current_location():
    try:
        from user_location import get_current_location
        return get_current_location
    except Exception as e:
        raise ImportError(f"Failed to import user_location module: {e}")



class LegacySearchRequest(BaseModel):
    keyword: str | None = None
    # Range selected on website in kilometers. If omitted, server uses default.
    range_km: int | None = None


class ClinicOut(BaseModel):
    # allow populating directly from SQLAlchemy ORM objects
    model_config = {"from_attributes": True}

    id: UUID
    place_id: str | None
    name: str
    registered: bool
    invited_count: int
    last_invited: datetime | None
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
    async def legacy_search(payload: LegacySearchRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
        """Call the existing run_system() using only the detected IP-based location."""
        keyword = payload.keyword or "Dermal fillers"

        get_current_location = _get_current_location()
        lat, lng = get_current_location()
        if not lat or not lng:
            raise HTTPException(status_code=500, detail="Location detection failed")

        try:
            legacy_main = _get_legacy_main()
            # If frontend provided a range (km), convert to meters and pass it
            max_radius_m = None
            if payload.range_km:
                try:
                    max_radius_m = int(payload.range_km) * 1000
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid range_km value")

            # Run the search in the background to allow immediate response
            background_tasks.add_task(legacy_main.run_system, lat, lng, keyword, max_radius_m=max_radius_m)
        except Exception as exc:  # pragma: no cover - legacy script errors surfaced to client
            # log the full traceback so the server log contains diagnostic data
            logger.exception("legacy search execution failed")
            raise HTTPException(status_code=500, detail=f"Legacy search failed: {exc}") from exc

        return {"status": "ok"}

    @app.get("/api/clinics/registered", response_model=list[ClinicOut])
    async def list_registered_clinics(
        db: AsyncSession = Depends(get_db),
        keyword: str | None = Query(None, description="Filter clinics by keyword (fuzzy match)"),
    ) -> list[ClinicOut]:
        try:
            query = select(Clinic).where(Clinic.registered == True)
            
            # Filter by exactly matching keyword if provided
            if keyword:
                # User wants exact matches for the predefined options
                # (e.g., "Dermal fillers", "Skin care", "Dental clinic")
                query = query.where(Clinic.keywords == keyword)
            
            query = query.order_by(Clinic.created_at.desc())
            result = await db.execute(query)
            clinics = result.scalars().all()
            # use fromattributes so conversion works correctly
            return [ClinicOut.model_validate(c) for c in clinics]
        except Exception as exc:
            logger.exception("error listing registered clinics")
            # return empty list on error so UI simply shows "no clinics";
            # the log will contain details if something went wrong
            return []

    return app


app = create_app()

