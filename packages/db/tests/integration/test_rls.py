import uuid

import pytest
from db.models import Base, Program, Tenant
from db.session import SessionLocal, db_session
from sqlalchemy import text


def test_rls_isolation(postgres_engine):
    Base.metadata.drop_all(postgres_engine)
    Base.metadata.create_all(postgres_engine)
    
    with postgres_engine.begin() as conn:
        conn.execute(text("ALTER TABLE programs ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text("CREATE POLICY tenant_isolation_policy ON programs USING (tenant_id = current_setting('app.tenant_id')::uuid);"))
        conn.execute(text("ALTER TABLE programs FORCE ROW LEVEL SECURITY;"))
        
    with postgres_engine.connect() as conn:
        # Create a non-superuser role to test RLS (superusers bypass RLS)
        conn.execute(text("COMMIT")) # End current implicit transaction
        try:
            conn.execute(text("CREATE ROLE app_user;"))
            conn.execute(text("COMMIT"))
        except Exception:
            conn.execute(text("ROLLBACK"))
            
        conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;"))
        conn.commit()

    tenant1 = uuid.uuid4()
    tenant2 = uuid.uuid4()

    with SessionLocal(bind=postgres_engine) as session:
        t1 = Tenant(id=tenant1, name='T1', slug='t1')
        t2 = Tenant(id=tenant2, name='T2', slug='t2')
        session.add(t1)
        session.add(t2)
        session.commit()

    with db_session(tenant1) as session:
        session.execute(text("SET ROLE app_user;"))
        p1 = Program(tenant_id=tenant1, name="Program 1")
        session.add(p1)
        session.commit()

    with db_session(tenant2) as session:
        session.execute(text("SET ROLE app_user;"))
        # Tenant 2 should not see Tenant 1's program
        programs = session.query(Program).all()
        assert len(programs) == 0
        
        p2 = Program(tenant_id=tenant2, name="Program 2")
        session.add(p2)
        session.commit()
        
        programs = session.query(Program).all()
        assert len(programs) == 1
        assert programs[0].name == "Program 2"
