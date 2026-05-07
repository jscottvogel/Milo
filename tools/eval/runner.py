import os
import yaml
import asyncio
import argparse
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, Tenant, User, Program, Thread, Milo
from db.session import db_session
from agent.runner import AgentRunner

engine = create_engine(os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def run_scenario(scenario_path: str):
    print(f"Running scenario: {scenario_path}")
    with open(scenario_path, "r") as f:
        scenario = yaml.safe_load(f)
        
    tenant_id = uuid.uuid4()
    thread_id = str(uuid.uuid4())
    
    # First create tenant using a raw session without RLS
    with SessionLocal() as session:
        tenant = Tenant(id=tenant_id, name="Eval Tenant", slug=f"eval-{tenant_id}")
        session.add(tenant)
        session.commit()
        
    # Now use db_session which sets RLS tenant_id
    with db_session(tenant_id) as session:
        milo = Milo(id=uuid.uuid4(), tenant_id=tenant_id, name="Test Milo", persona_pack="sme")
        session.add(milo)
        session.flush() # Ensure milo exists before thread
        
        thread = Thread(id=thread_id, tenant_id=tenant_id, milo_id=milo.id)
        session.add(thread)
        session.commit()
        
        runner = AgentRunner(session=session, tenant_id=str(tenant_id), thread_id=thread_id, milo_id=str(milo.id))
        
        for turn in scenario.get("turns", []):
            user_msg = turn.get("user")
            print(f"User: {user_msg}")
            
            response = ""
            async for event in runner.run_turn(user_msg):
                if event["type"] == "token":
                    response += event["content"]
                    print(event["content"], end="", flush=True)
            print("\n")
            
            expected = turn.get("expected", {})
            if "response_contains" in expected:
                assert expected["response_contains"].lower() in response.lower(), f"Expected '{expected['response_contains']}' in response"
                
    # Clean up with raw session
    with SessionLocal() as session:
        session.execute(Thread.__table__.delete().where(Thread.id == thread_id))
        session.execute(Milo.__table__.delete().where(Milo.id == milo.id))
        session.execute(Tenant.__table__.delete().where(Tenant.id == tenant_id))
        session.commit()
    print("Passed!\n")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-starters", action="store_true")
    args = parser.parse_args()
    
    scenario_dir = os.path.join(os.path.dirname(__file__), "scenarios")
    
    if args.all_starters:
        files = [f for f in os.listdir(scenario_dir) if f.endswith(".yaml")]
        for f in files:
            await run_scenario(os.path.join(scenario_dir, f))

if __name__ == "__main__":
    asyncio.run(main())
