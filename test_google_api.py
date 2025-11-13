import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env")
    exit(1)

print(f"Testing API key: {api_key[:10]}...")

# Test 1: Standard Gemini API
print("\n1. Testing standard Gemini API...")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

response = requests.post(
    url,
    headers={"Content-Type": "application/json"},
    json={
        "contents": [{
            "parts": [{"text": "Say hello"}]
        }]
    }
)

if response.status_code == 200:
    print("✅ Standard API works!")
    print(f"Response: {response.json()['candidates'][0]['content']['parts'][0]['text']}")
else:
    print(f"❌ Standard API failed: {response.status_code}")
    print(f"Error: {response.text}")

# Test 2: List available models
print("\n2. Testing model list API...")
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

response = requests.get(url)

if response.status_code == 200:
    models = response.json().get('models', [])
    print(f"✅ Model list API works! Found {len(models)} models")
    # Show some model names
    model_names = [m['name'] for m in models[:5]]
    print(f"Sample models: {', '.join(model_names)}")
else:
    print(f"❌ Model list API failed: {response.status_code}")
    print(f"Error: {response.text}")

# Test 3: Check if Realtime API models are available
print("\n3. Checking for Realtime API models...")
realtime_models = [m for m in models if 'realtime' in m.get('name', '').lower() or '2.0' in m.get('name', '')]
if realtime_models:
    print(f"✅ Found {len(realtime_models)} Realtime-capable models:")
    for model in realtime_models[:3]:
        print(f"   - {model['name']}")
else:
    print("⚠️  No Realtime models found in list")