import urllib.request
import json

queries = [
    # Should be Knowledge
    "Working Hours",
    "How many earned leaves?",
    
    # Multi-Intent Queries
    "Hi company name",
    "Hello HR policy",
    "Hey working hours",
    "Good morning leave policy",
    "Hello contact HR",
    "Hi technology stack",
    "Hello AI services",
    "Namaste company address",
    "Good evening frontend framework",
    "Hi what is Mobiloitte?",
    
    # Should be Gibberish
    "gtgb",
    "nkio",
    "eoipmk",
    
    # Should be Fallback
    "Who is Elon Musk?",
    "Weather today",
    "IPL Winner"
]

for query in queries:
    print(f"\n--- Query: {query} ---")
    data = json.dumps({"message": query, "session_id": "123", "conversation_id": "123", "metadata": {}}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8000/chat", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            print("Response:", res_data.get("response"))
    except urllib.error.HTTPError as e:
        print("Error HTTP", e.code)
        print(e.read().decode("utf-8"))
    except Exception as e:
        print("Error:", str(e))
