import os
import asyncio
from agent.graph import build_graph
from langgraph.checkpoint.memory import MemorySaver

async def main():
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    os.environ["AWS_PROFILE"] = "AdministratorAccess-520477993393"
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer)
    
    tenant_id = "00000000-0000-0000-0000-000000000001"
    config = {"configurable": {"tenant_id": tenant_id}}
    
    try:
        from db.session import SessionLocal
        from db.models.program import WorkItem
        from sqlalchemy import select
        with SessionLocal() as db:
            p = db.execute(select(WorkItem).where(WorkItem.name.like("Milo Platform%"))).scalar_one_or_none()
            pid = str(p.id) if p else "milo-platform"
            
        print(f"Triggering for program {pid}...")
        
        inputs = {"messages": [("user", f"Compute the critical path for program {pid}")]}
        async for output in graph.astream(inputs, config=config, stream_mode="values"):
            for key, value in output.items():
                print(f"Output from node '{key}':")
                print("---")
                if isinstance(value, list) and len(value) > 0:
                    print(value[-1].content)
                else:
                    print(value)
            print("\n---\n")
    except Exception as e:
        print("EXCEPTION:", type(e), e)

if __name__ == "__main__":
    asyncio.run(main())
