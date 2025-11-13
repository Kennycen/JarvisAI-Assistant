import requests
import json

BASE_URL = "http://localhost:5000"

# Test health endpoint
print("Testing /api/health...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Raw response text: {response.text}")
    print(f"Response length: {len(response.text)}")
    
    if response.status_code == 200:
        print(f"JSON Response: {response.json()}")
    else:
        print(f"Non-200 status. Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print(f"Response was: {response.text}")

print("\n" + "="*50 + "\n")

# Test create-room endpoint
print("Testing /api/create-room...")
try:
    response = requests.post(
        f"{BASE_URL}/api/create-room",
        json={"participant_name": "test_user"}
    )
    print(f"Status: {response.status_code}")
    print(f"Raw response text: {response.text}")
    
    if response.status_code == 200:
        print(f"JSON Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Non-200 status. Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print(f"Response was: {response.text}")