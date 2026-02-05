import requests
from datetime import datetime
from servers import SERVERS
import json

def ts(ms):
    if not ms or ms == 0:
        return "∞"
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M")

dump = []

for srv in SERVERS:
    s = requests.Session()
    s.post(f"{srv['host']}/login", data=srv["auth"])

    resp = s.get(f"{srv['host']}/panel/api/inbounds/list").json()
    inbounds = resp.get("obj", [])

    for inbound in inbounds:
        inbound_obj = {
            "server": srv["name"],
            "id": inbound["id"],
            "protocol": inbound.get("protocol"),
            "port": inbound.get("port"),
            "remark": inbound.get("remark"),
            "expiry": ts(inbound.get("expiryTime")),
            "traffic_gb": round(inbound.get("allTime", 0) / 1024**3, 2),
            "clients": []
        }


        settings = json.loads(inbound.get("settings", "{}"))
        clients_cfg = settings.get("clients", [])
        comments = {
            c.get("email"): c.get("comment")
            for c in clients_cfg
        }


        for c in inbound.get("clientStats", []):
            inbound_obj["clients"].append({
                "comment": comments.get(c.get("email")),
                "email": c.get("email"),
                "uuid": c.get("uuid"),
                "enable": c.get("enable"),
                "expiry": ts(
                    c.get("expiryTime")
                    if c.get("expiryTime", 0) > 0
                    else inbound.get("expiryTime")
                ),
                "traffic_gb": round(c.get("allTime", 0) / 1024**3, 2),
                "lastOnline": ts(c.get("lastOnline"))
            })

        dump.append(inbound_obj)

with open("3xui_dump.json", "w", encoding="utf-8") as f:
    json.dump(dump, f, ensure_ascii=False, indent=2)
