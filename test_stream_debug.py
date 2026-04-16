"""测试 /api/chat/stream 接口"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx
import time

# 1. 登录
login_resp = httpx.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "123456"},
    timeout=10,
)
token = login_resp.json()["data"]["access_token"]
user_id = login_resp.json()["data"]["user_id"]
print(f"[OK] login success, user_id={user_id}")

# 2. 获取 threads
threads_resp = httpx.get(
    "http://localhost:8000/api/threads?page=1&page_size=10",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)
threads_data = threads_resp.json()
threads_list = threads_data["data"]["threads"]
print(f"[OK] threads count: {len(threads_list)}")
thread_id = threads_list[0]["id"] if threads_list else None

if not thread_id:
    create_resp = httpx.post(
        "http://localhost:8000/api/threads",
        headers={"Authorization": f"Bearer {token}"},
        json={},
        timeout=10,
    )
    thread_id = create_resp.json()["data"]["thread"]["id"]
    print(f"[OK] created new thread: {thread_id}")

print(f"[OK] using thread_id={thread_id}")

# 3. 测试 stream
print("")
print("=== Testing /api/chat/stream ===")

start = time.time()
try:
    with httpx.stream(
        "POST",
        "http://localhost:8000/api/chat/stream",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"thread_id": thread_id, "message": "hello"},
        timeout=60,
    ) as response:
        print(f"[RESP] status: {response.status_code}")
        print(f"[RESP] content-type: {response.headers.get('content-type', 'N/A')}")
        print(f"[RESP] waiting for stream data...")
        
        for line in response.iter_lines():
            elapsed = time.time() - start
            print(f"  [{elapsed:.2f}s] {line}")
            
except Exception as e:
    elapsed = time.time() - start
    print(f"[ERROR] [{elapsed:.2f}s] {type(e).__name__}: {e}")

print("=" * 60)
print(f"Total time: {time.time() - start:.2f}s")
