from db.session import engine
from sqlalchemy import text
from db.models.base import Base
import db.models

with engine.connect() as conn:
    conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public; CREATE EXTENSION IF NOT EXISTS vector;'))
    conn.commit()

Base.metadata.create_all(engine)
print('Database rebuilt successfully.')
