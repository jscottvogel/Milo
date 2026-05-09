import httpx
import asyncio
import json

async def main():
    async with httpx.AsyncClient() as client:
        token = "dev_00000000-0000-0000-0000-000000000001"
        headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": "00000000-0000-0000-0000-000000000001"}
        
        print("Logged in, sending message...")
        
        import uuid
        thread_id = str(uuid.uuid4())
        
        async with client.stream("POST", f"http://localhost:8000/v1/threads/{thread_id}/messages", headers=headers, json={"content": "Compute the critical path for the Milo Platform program"}) as response:
            async for line in response.aiter_lines():
                print(line)

if __name__ == "__main__":
    asyncio.run(main())
