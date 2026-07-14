import requests
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "message": "hello",
    "session_id": "test_session_123",
    "conversation_id": "test_conv_123",
    "metadata": {}
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
