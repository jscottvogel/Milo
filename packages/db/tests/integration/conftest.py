
import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="session")
def postgres_engine():
    # Use the manually started milo-db-dev container
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/postgres")

    # We need to manually add the extension for the test DB
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

    return engine
