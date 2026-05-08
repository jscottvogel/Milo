from db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE commitments ADD COLUMN owner_name VARCHAR;'))
        conn.commit()
        print("Successfully added owner_name column to commitments.")
    except Exception as e:
        print(f"Migration failed or column already exists: {e}")
