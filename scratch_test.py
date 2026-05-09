import httpx
import asyncio

async def test_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/threads/00000000-0000-0000-0000-000000000001/messages",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dev_00000000-0000-0000-0000-000000000001",
                "Origin": "http://localhost:3000"
            },
            json={"content": "Context: Home\n\nHello"}
        )
        print("Status Code:", response.status_code)
        print("Headers:", response.headers)
        print("Response Text:", response.text)

asyncio.run(test_endpoint())
