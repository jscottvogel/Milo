import contextlib
import uuid
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Session, "after_begin")
def receive_after_begin(session: Session, transaction, connection):
    tenant_id = session.info.get("tenant_id")
    if tenant_id:
        connection.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))


@contextlib.contextmanager
def db_session(tenant_id: str | uuid.UUID) -> Generator[Session, None, None]:
    """Yields a database session scoped to a specific tenant."""
    session = SessionLocal()
    session.info["tenant_id"] = str(tenant_id)
    # The after_begin event will apply the SET LOCAL upon transaction start
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@event.listens_for(Session, "before_commit")
def check_tenant_id(session: Session, *args, **kwargs) -> None:
    # We could add an event listener here to strictly ensure app.tenant_id is set
    # if it's a requirement to block any queries without it, but Postgres RLS
    # will naturally block reads/writes if it's missing on RLS-enabled tables.
    pass
