import requests
import json
payload = {
    "power_settings": {
        "interval_min": 120,
        "active_start_hour": None,
        "active_end_hour": None,
        "runtime_min": None
    }
}
r = requests.post("http://127.0.0.1:8080/api/save_config", json=payload)
print(r.status_code, r.text)
r = requests.get("http://127.0.0.1:8080/api/get_config")
print(json.loads(r.text).get('power_settings'))
