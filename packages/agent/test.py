import asyncio
import logging
from agent.runner import AgentRunner
from db.session import SessionLocal

logging.basicConfig(level=logging.DEBUG)

async def main():
    db = SessionLocal()
    runner = AgentRunner(
        session=db,
        tenant_id='00000000-0000-0000-0000-000000000001',
        thread_id='123e4567-e89b-12d3-a456-426614174000',
        milo_id='00000000-0000-0000-0000-000000000001' # might fail if local milo has different uuid, but thread already ran with context
    )
    # Get milo id from db
    from db.models.identity import Milo
    milo = db.query(Milo).filter(Milo.tenant_id == '00000000-0000-0000-0000-000000000001').first()
    if milo:
        runner.milo_id = str(milo.id)
    else:
        print("No milo")
        return

    stream = runner.run_turn('Please create a sample program')
    async for evt in stream:
        print(evt)

asyncio.run(main())
