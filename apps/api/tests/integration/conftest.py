import pytest
from db.models import Base
from sqlalchemy import create_engine


# Assuming local DB for tests since testcontainers is disabled
@pytest.fixture(scope="session")
def postgres_engine():
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    return engine

@pytest.fixture(autouse=True)
def setup_db(postgres_engine):
    Base.metadata.create_all(postgres_engine)
    return
    # Could drop tables here, but skipping for speed in PoC mode
