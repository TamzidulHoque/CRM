This is faces app CRM test project.

## Category sorting 
1. All the clinics are not sorted according to category while showing on the registered place
2.  The category options should be bound in specific option bar for correctly sorting in database. 


## Data Storage

Legacy artifacts such as the JSON tracker files and the `bin/`
directory have been removed entirely.  State is now persisted in the
PostgreSQL database using SQLAlchemy, and any auxiliary scripts have been
refactored or discarded to keep the repository focused on production code.

Before running `main.py` you should ensure the database exists and the
migrations have been applied (`backend/alembic` is configured to manage
schema changes). The connection URL defaults to
`postgresql+asyncpg://postgres:postgres@localhost:5432/faces_crm` but can be
overridden via an `.env` file using the `DATABASE_URL` variable.

The two relevant tables are:

- `registered_clinics` – names of clinics that should stop the search loop
  as soon as they are seen.
- `clinic_leads` – every clinic encountered while searching ends up here;
  it also carries `last_invited_at`/`invite_count` information previously
  stored in `email_log.json`.

The helper functions exposed by `storage.py` (`load_registered`,
`save_registered`, `can_send_email_to_clinic`, `mark_email_sent_to_clinic` and
`record_clinic`) wrap simple queries/updates against these tables.

> **Note:** if you hit a 500 error when calling `/api/legacy-search` the
> underlying cause is usually a schema mismatch (for example the
> `registered_clinics` table missing the `name` column).  Make sure the
> database has been initialised and migrations applied (`alembic upgrade head`) or
> the endpoint will raise an exception when the legacy code tries to read
> the registry.  The application now traps this failure and returns an empty
> list, but the migration should still be run during setup.