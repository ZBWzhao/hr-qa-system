import sys
import requests

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/v1"
r = requests.post(base + "/auth/login", json={"username": "zhangsan", "password": "123456"})
print("login", r.status_code)
if r.status_code != 200:
    print(r.text)
    raise SystemExit(1)

token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

question = "我们公司有什么福利吗？"
r2 = requests.post(
    base + "/chat",
    json={"question": question},
    headers=headers,
    timeout=60,
)
print("chat", r2.status_code)
print(r2.text[:3000])
