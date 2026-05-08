from db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE stakeholders ADD COLUMN satisfaction VARCHAR;'))
        conn.commit()
        print("Successfully added satisfaction column.")
    except Exception as e:
        print(f"Migration failed or column already exists: {e}")
