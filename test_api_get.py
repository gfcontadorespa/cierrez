import requests

try:
    res = requests.get("http://localhost:8000/api/cierres")
    print("GET /api/cierres Status:", res.status_code)
except Exception as e:
    print("Exception:", e)

try:
    res = requests.get("http://localhost:8000/api/branches")
    print("GET /api/branches Status:", res.status_code)
except Exception as e:
    print("Exception:", e)
