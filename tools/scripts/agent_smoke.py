import sys
import httpx
import json
import uuid

def smoke_test(message: str):
    thread_id = str(uuid.uuid4())
    url = f"http://localhost:8000/v1/threads/{thread_id}/messages"
    
    # Needs a valid UUID for the tenant
    tenant_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer dev_{tenant_id}"}
    payload = {"content": message}
    
    print(f"Sending message to thread {thread_id}...\n")
    
    try:
        with httpx.stream("POST", url, headers=headers, json=payload, timeout=30.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data["type"] == "token":
                        print(data["content"], end="", flush=True)
                    elif data["type"] == "usage":
                        print(f"\n\n[Cost: ${data['metrics']['cost_usd']:.5f}]")
                    elif data["type"] == "done":
                        print("\n[Stream Complete]")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(e.response.text)

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hello, who are you?"
    smoke_test(msg)
