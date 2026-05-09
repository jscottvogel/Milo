import asyncio
import os
from agent.runner import AgentRunner
from db.session import SessionLocal

async def main():
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    os.environ["AWS_PROFILE"] = "AdministratorAccess-520477993393"
    
    tenant_id = "00000000-0000-0000-0000-000000000001"
    milo_id = "11111111-1111-1111-1111-111111111111"
    thread_id = "22222222-2222-2222-2222-222222222222"
    
    db = SessionLocal()
    runner = AgentRunner(session=db, tenant_id=tenant_id, thread_id=thread_id, milo_id=milo_id)
    
    try:
        print("Running agent turn...")
        async for event in runner.run_turn("Compute the critical path for the Milo Platform program"):
            print("Event:", event)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
