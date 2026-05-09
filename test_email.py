import asyncio
from dotenv import load_dotenv
import os
import sys

# Add apps/api to path so we can import things
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/api"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../packages/db"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../packages/agent"))

os.environ["DATABASE_URL"] = "postgresql+psycopg://milo_user:milo_password@localhost:5432/milo"
load_dotenv()

from db.session import SessionLocal
from agent.runner import AgentRunner
from db.models.identity import Tenant, Milo
from agent.tools.registry import registry
from agent.tools.context import AgentContext

async def test():
    with SessionLocal() as session:
        tenant_id = "00000000-0000-0000-0000-000000000001"
        milo_id = "00000000-0000-0000-0000-000000000100"
            
        runner = AgentRunner(session, tenant_id, "test-thread", milo_id)
        
        tool = registry.get_tool("email.send")
        context = AgentContext(session, tenant_id, milo_id, "test-thread", runner.integration_tokens)
        
        print(f"Integration tokens: {runner.integration_tokens}")
        
        result = await tool.invoke({"to": "scott@scott-s-organization.nylas.email", "subject": "Test from Milo", "body": "This is a test."}, context)
        print("Result:", result)

asyncio.run(test())
