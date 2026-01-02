import requests
import json

BASE_URL = "https://todavia.tilcanet.com.ar/api"

# 1. Login Aliado
def login_aliado():
    print("Intento de Login de Aliado...")
    try:
        resp = requests.post(f"{BASE_URL}/aliado/login/", json={
            "username": "admin", # Cambiar si tienes otro
            "password": "admin"
        })
        if resp.status_code == 200:
            print("Login OK:", resp.json())
            return resp.json()['aliado_id']
        else:
            print("Error Login:", resp.status_code, resp.text)
            return None
    except Exception as e:
        print("Excepción Login:", e)
        return None

# 2. Obtener Chats
def get_chats(aliado_id):
    print(f"Buscando chats para aliado {aliado_id}...")
    try:
        resp = requests.get(f"{BASE_URL}/aliado/{aliado_id}/chats/")
        if resp.status_code == 200:
            chats = resp.json()['sesiones']
            print(f"Chats encontrados: {len(chats)}")
            if len(chats) > 0:
                return chats[0]['sesion_id']
            return None
        else:
            print("Error Get Chats:", resp.status_code, resp.text)
            return None
    except Exception as e:
        print("Excepción Chats:", e)
        return None

# 3. Enviar Mensaje
def send_message(sesion_id):
    print(f"Enviando mensaje a sesión {sesion_id}...")
    try:
        resp = requests.post(f"{BASE_URL}/aliado/chat/{sesion_id}/mensajes/", json={
            "texto": "Mensaje de prueba desde script debug"
        })
        if resp.status_code == 200:
            print("Mensaje enviado OK")
        else:
            print("Error Enviar Mensaje:", resp.status_code, resp.text)
    except Exception as e:
        print("Excepción Enviar:", e)

if __name__ == "__main__":
    aliado_id = login_aliado()
    if aliado_id:
        sesion_id = get_chats(aliado_id)
        if sesion_id:
            send_message(sesion_id)
        else:
            print("No hay sesiones activas para probar envío.")
    else:
        print("No se pudo loguear.")
