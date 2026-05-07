# Milo Database Package

This package (`packages/db`) contains all SQLAlchemy models, Alembic migrations, and session management logic for the Milo platform.

## Development

### Adding a new model
1. Define your model in `db/models/`.
2. Ensure it inherits from `TenantBoundBase` if it contains tenant-specific data.
3. Add the model to `db/models/__init__.py`.
4. Run `uv run alembic revision --autogenerate -m "Add X model"` to generate the migration.
5. Apply the migration locally with `uv run alembic upgrade head`.

### Working with the Database Session
Always use the `db_session` context manager when querying tenant data. This automatically sets the `app.tenant_id` session variable in Postgres, which enforces our Row-Level Security (RLS) policies.

```python
from db.session import db_session
from db.models import Program

with db_session(tenant_id="123e4567-e89b-12d3-a456-426614174000") as session:
    # This query will ONLY return programs for the specified tenant_id,
    # even if we didn't explicitly filter by it!
    programs = session.query(Program).all()
```

### Seeding Data
To seed a local database with development data:
```bash
uv run python ../../tools/seed/seed_dev.py
```
