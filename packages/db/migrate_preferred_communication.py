from db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN preferred_communication VARCHAR DEFAULT 'email';"))
        print("Added preferred_communication to users.")
    except Exception as e:
        print(f"User migration failed: {e}")

    try:
        conn.execute(text("ALTER TABLE stakeholders ADD COLUMN preferred_communication VARCHAR DEFAULT 'email';"))
        print("Added preferred_communication to stakeholders.")
    except Exception as e:
        print(f"Stakeholder migration failed: {e}")

    conn.commit()
