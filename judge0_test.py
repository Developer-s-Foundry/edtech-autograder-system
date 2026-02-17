import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv("JUDGE0_BASE_URL")
KEY  = os.getenv("JUDGE0_API_KEY")
HOST = os.getenv("JUDGE0_RAPIDAPI_HOST")

headers = {
    "X-RapidAPI-Key": KEY,
    "X-RapidAPI-Host": HOST,
    "Content-Type": "application/json",
}

payload = {
    "source_code": "print('Hello from Judge0')",
    "language_id": 71
}

# Step 1: Submit code
response = requests.post(
    f"{BASE}/submissions?base64_encoded=false&wait=false",
    json=payload,
    headers=headers
)

response.raise_for_status()
token = response.json()["token"]
print("Submission token:", token)

# Step 2: Get result
result = requests.get(
    f"{BASE}/submissions/{token}?base64_encoded=false",
    headers=headers
)

print("Result:", result.json())
