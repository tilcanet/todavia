import requests
import json
import uuid

BASE_URL = "https://todavia.tilcanet.com.ar/api"

def test_user_flow():
    # 1. Generate a UUID locally (mimicking the app)
    user_id = str(uuid.uuid4())
    print(f"Testing with User ID: {user_id}")
    
    # 2. Register (Optional in theory if we just want to chat, but good practice)
    # The app calls /usuario/<id>/alias/ to register/update
    print("Step 1: Registering/Updating Alias...")
    try:
        resp = requests.post(f"{BASE_URL}/usuario/{user_id}/alias/", json={
            "alias": "TestUser",
            "dispositivo_modelo": "Python Script",
            "dispositivo_os": "Windows"
        })
        print(f"Register Status: {resp.status_code}")
        print(f"Register Response: {resp.text}")
    except Exception as e:
        print(f"Register Failed: {e}")
        return

    # 3. Send Message
    print("\nStep 2: Sending Chat Message...")
    try:
        resp = requests.post(f"{BASE_URL}/chat/{user_id}/", json={
            "texto": "Hola, me siento un poco solo hoy."
        })
        print(f"Chat Status: {resp.status_code}")
        print(f"Chat Response: {resp.text}")
    except Exception as e:
        print(f"Chat Failed: {e}")

if __name__ == "__main__":
    test_user_flow()
