import requests
import json

BASE_URL = "https://todavia.tilcanet.com.ar/api"

def check_production_health():
    print(f"Checking Production: {BASE_URL}")
    
    # 1. Test Ally Login
    print("\n--- 1. Testing Ally Login (admin/admin) ---")
    try:
        resp = requests.post(f"{BASE_URL}/aliado/login/", json={
            "username": "admin",
            "password": "admin"
        })
        if resp.status_code == 200:
            print("LOGIN SUCCESS!")
            data = resp.json()
            print(f"Ally ID: {data.get('aliado_id')}")
            print(f"Available: {data.get('esta_disponible')}")
            return data.get('aliado_id')
        else:
            print(f"LOGIN FAILED. Status: {resp.status_code}")
            print(f"Reason: {resp.text}")
            return None
    except Exception as e:
        print(f"Excepcion: {e}")
        return None

def check_active_chats(aliado_id):
    if not aliado_id: return
    print(f"\n--- 2. Checking Active Chats for Ally {aliado_id} ---")
    try:
        resp = requests.get(f"{BASE_URL}/aliado/{aliado_id}/chats/")
        print(f"Status: {resp.status_code}")
        print(f"Data: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    aliado_id = check_production_health()
    if aliado_id:
        check_active_chats(aliado_id)
