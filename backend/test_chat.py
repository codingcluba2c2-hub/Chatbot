import urllib.request
import json
import traceback

data = json.dumps({"message": "Tell me HR policy", "session_id": "123", "conversation_id": "123", "metadata": {}}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8000/chat", data=data, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as response:
        print("STATUS:", response.status)
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("STATUS:", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
