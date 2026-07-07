import sys
import requests

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/v1"
r = requests.post(base + "/auth/login", json={"username": "zhangsan", "password": "123456"})
token = r.json()["data"]["access_token"]
r2 = requests.post(
    base + "/chat",
    json={"question": "我们公司有什么福利吗？"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=60,
)
print("status", r2.status_code)
print("headers", dict(r2.headers))
print("body", r2.text[:5000])
