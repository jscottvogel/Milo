import os
import asyncio
from agent.tools.program import ProgramCriticalPathTool
import uuid

class MockSession:
    def scalars(self, stmt):
        class MockResult:
            def all(self):
                from sqlalchemy import create_engine, select
                from sqlalchemy.orm import Session
                from db.models.program import WorkItem
                db_url = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
                engine = create_engine(db_url)
                with Session(engine) as db:
                    return db.execute(select(WorkItem)).scalars().all()
        return MockResult()

class MockContext:
    tenant_id = "00000000-0000-0000-0000-000000000001"
    session = MockSession()

async def main():
    tool = ProgramCriticalPathTool()
    try:
        res = await tool.invoke({'program_id': '1592a936-33a5-46f6-a572-cfa169803152', 'what_if_slip_days': 14, 'what_if_task_id': 'some-task-id'}, MockContext())
        print("Success:", res.keys())
    except Exception as e:
        print("Error:", type(e), e)

if __name__ == "__main__":
    asyncio.run(main())
