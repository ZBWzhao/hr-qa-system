import sys
import requests

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8002/api/v1"
r = requests.post(base + "/auth/login", json={"username": "zhangsan", "password": "123456"})
token = r.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# list conversations
r_conv = requests.get(base + "/chat/conversations", headers=headers)
convs = r_conv.json().get("data", {}).get("items") or r_conv.json().get("data") or []
print("conversations", len(convs) if isinstance(convs, list) else type(convs))

conv_ids = []
if isinstance(convs, list):
    for c in convs[:5]:
        cid = c.get("conversation_id") if isinstance(c, dict) else None
        if cid:
            conv_ids.append(cid)
elif isinstance(convs, dict):
    for group in convs.values():
        if isinstance(group, list):
            for c in group:
                cid = c.get("conversation_id")
                if cid:
                    conv_ids.append(cid)

for cid in conv_ids[:3]:
    r2 = requests.post(
        base + "/chat",
        json={"question": "我们公司有什么福利吗？", "conversation_id": cid},
        headers=headers,
        timeout=60,
    )
    print("conv", cid, "status", r2.status_code)
    if r2.status_code != 200:
        print(r2.text[:200])
