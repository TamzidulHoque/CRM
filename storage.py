"""Persistent storage operations for clinic tracking.

All state is stored in the PostgreSQL ``clinics`` table. This module provides
helpers that abstract away the query details so the orchestration logic in
``operations.py`` remains simple.
"""
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# reuse the settings and models from the backend portion of the repo
from backend.app.settings import get_settings
from backend.app.models import Clinic


@lru_cache(maxsize=1)
def _get_sessionmaker():
    """Create a synchronous ``Session`` factory backed by PostgreSQL.

    The backend application uses an *async* engine, so its URL contains
    ``+asyncpg``.  ``create_engine`` does not understand that dialect,
    so we drop the suffix here.  ``lru_cache`` keeps one engine per
    process and avoids recreating it on every call.
    """

    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        sync_url = db_url.replace("+asyncpg", "")
    else:
        sync_url = db_url

    engine = create_engine(sync_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Lookup and listing
# ---------------------------------------------------------------------------

def load_registered() -> list[str]:
    """Return a list of clinic names marked as registered.

    Pre-migration or schema issues are tolerated by returning an empty list
    so that callers (the legacy search loop) behave as if no clinics have
    registered yet.
    """

    Session = _get_sessionmaker()
    try:
        with Session() as session:
            return session.scalars(
                select(Clinic.name).where(Clinic.registered == True)
            ).all()
    except Exception:  # pragma: no cover - defensive fallback
        print("storage.load_registered: database query failed, returning []")
        return []


# ---------------------------------------------------------------------------
# Recording and tracking
# ---------------------------------------------------------------------------

def save_searched_clinic_data(clinic_data: dict, keyword: str, emails: list[str]) -> None:
    """Save all discovered clinic data into the database.
    
    Creates or updates a clinic record using place_id or name as the primary identifier.
    """
    Session = _get_sessionmaker()
    with Session() as session:
        place_id = clinic_data.get("place_id")
        name = clinic_data.get("name")
        
        if not name:
            return
            
        clinic = None
        if place_id:
            clinic = session.scalar(select(Clinic).where(Clinic.place_id == place_id))
        if clinic is None:
            clinic = session.scalar(select(Clinic).where(Clinic.name == name))
            
        if clinic is None:
            clinic = Clinic(name=name, registered=False)
            session.add(clinic)
            
        # Update identity
        if place_id and not clinic.place_id:
            clinic.place_id = place_id
            
        phone_number = clinic_data.get("phone_number")
        if phone_number and phone_number not in (clinic.phone or []):
            clinic.phone = list(clinic.phone or []) + [phone_number]
            
        website = clinic_data.get("website")
        if website:
            clinic.website = website
            
        # Update keywords
        if keyword and keyword not in (clinic.keywords or []):
            clinic.keywords = list(clinic.keywords or []) + [keyword]
            
        # Update emails
        existing_emails = set(clinic.emails or [])
        new_emails = list(existing_emails.union(set(emails)))
        clinic.emails = new_emails
        
        # Update location info
        location_info = dict(clinic.clinic_location or {})
        location_info.update({
            "address": clinic_data.get("address"),
            "latitude": clinic_data.get("latitude"),
            "longitude": clinic_data.get("longitude"),
            "rating": clinic_data.get("rating"),
            "opening_hours": clinic_data.get("opening_hours"),
            "reviews": clinic_data.get("reviews"),
            "google_maps_link": clinic_data.get("google_maps_link"),
        })
        # Remove None values
        clinic.clinic_location = {k: v for k, v in location_info.items() if v is not None}
        
        session.commit()


def save_registered(clinic_name: str) -> None:
    """Mark a clinic as registered.

    This updates the ``registered`` flag to True. If the clinic record does
    not yet exist it is created.
    """

    Session = _get_sessionmaker()
    with Session() as session:
        clinic = session.scalar(
            select(Clinic).where(Clinic.name == clinic_name)
        )
        if clinic is None:
            clinic = Clinic(name=clinic_name, registered=True)
            session.add(clinic)
        else:
            clinic.registered = True
        session.commit()


# ---------------------------------------------------------------------------
# Email invitation tracking
# ---------------------------------------------------------------------------

def can_send_email_to_clinic(clinic_name: str, cooldown_days: int = 30) -> bool:
    """Return True if enough time has elapsed since the last email invite.

    If a clinic has never been invited or has no record yet, the function
    returns True so that the first email attempt can be made.
    """

    Session = _get_sessionmaker()
    with Session() as session:
        clinic = session.scalar(
            select(Clinic).where(Clinic.name == clinic_name)
        )
        if clinic is None or clinic.last_invited is None:
            return True

        now = datetime.now(timezone.utc)
        return now - clinic.last_invited >= timedelta(days=cooldown_days)


def mark_email_sent_to_clinic(clinic_name: str, email: str = None) -> None:
    """Record that an invitation email was sent to a clinic.

    Updates the ``invited_count`` and ``last_invited`` timestamp. If the
    clinic record does not exist yet it is created.
    """

    Session = _get_sessionmaker()
    with Session() as session:
        clinic = session.scalar(
            select(Clinic).where(Clinic.name == clinic_name)
        )
        now = datetime.now(timezone.utc)

        if clinic is None:
            # Create a new record for this clinic
            clinic = Clinic(
                name=clinic_name,
                invited_count=1,
                last_invited=now,
                registered=False,
            )
            if email:
                clinic.emails = [email]
            session.add(clinic)
        else:
            # Update existing record
            clinic.invited_count = (clinic.invited_count or 0) + 1
            clinic.last_invited = now
            # Add email if provided and not already present
            if email and email not in (clinic.emails or []):
                clinic.emails = (clinic.emails or []) + [email]

        session.commit()

