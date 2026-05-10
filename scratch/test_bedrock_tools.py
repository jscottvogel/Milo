import sys
sys.path.insert(0, 'c:/Users/j_sco/projects/Milo/Milo/apps/api')
import asyncio
from agent.runner import AgentRunner
from db.models.identity import Tenant, Milo
from db.models.agent import Thread
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings

async def test():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"): db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql+asyncpg://"): db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    engine = create_engine(db_url)
    with Session(engine) as db:
        milo = db.execute(select(Milo)).scalars().first()
        runner = AgentRunner(
            session=db,
            tenant_id=str(milo.tenant_id),
            thread_id=str(db.execute(select(Thread)).scalars().first().id),
            milo_id=str(milo.id)
        )
        tools = runner._format_tools_for_bedrock()
        
        from agent.llm.bedrock import BedrockClient
        client = BedrockClient()
        try:
            gen = client.invoke_with_streaming(
                messages=[{"role": "user", "content": [{"text": "Hello"}]}],
                system="system",
                tools=tools
            )
            async for _ in gen:
                pass
            print("Success")
        except Exception as e:
            print(f"Error: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(test())
