import traceback
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

# login
r = client.post("/api/v1/auth/login", json={"username": "zhangsan", "password": "123456"})
print("login", r.status_code, r.json().get("code"))
token = r.json()["data"]["access_token"]

# chat
try:
    r2 = client.post(
        "/api/v1/chat",
        json={"question": "我们公司有什么福利吗？"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("chat", r2.status_code)
    print(r2.text[:3000])
except Exception:
    traceback.print_exc()
