import urllib.request
try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/api/admin/greetings')
    print(response.read().decode())
except Exception as e:
    print("ERROR:", e)
