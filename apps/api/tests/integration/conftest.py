import pytest
from sqlalchemy import create_engine
from db.models import Base

# Assuming local DB for tests since testcontainers is disabled
@pytest.fixture(scope="session")
def postgres_engine():
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    yield engine

@pytest.fixture(autouse=True)
def setup_db(postgres_engine):
    Base.metadata.create_all(postgres_engine)
    yield
    # Could drop tables here, but skipping for speed in PoC mode
